import json
import os
from typing import Any, Optional, Union, Dict, Type, Tuple
from ignite import engine, handlers
from torch import nn, cuda, optim
import dataclasses as dc
import torch as th
import math
import csv

from env import logging
import pipeline as pipe
import constants as ct
import models


class Run(object):
    iterations: Union[float, int]
    log_interval: int
    evaluator: engine.Engine
    trainer: engine.Engine
    device: object
    metrics: Dict[str, Any]
    data_bunch: pipe.SmthDataBunch
    criterion: nn.CrossEntropyLoss
    optimizer: Union[optim.Adam, optim.SGD, optim.RMSprop]
    model: nn.Module
    epochs: int
    resume_from: Optional[str]
    resume: bool
    name: str

    logger: logging.Logger

    def __init__(self, opts: models.RunOptions):
        self.__init_record(opts)
        self.logger = self.__init_logging(opts.name)
        self.logger.info(f'Initializing run {opts.name}.')

        self.name = opts.name
        self.resume = opts.resume
        self.resume_from = opts.resume_from
        self.epochs = opts.trainer_opts.epochs

        self.model = self.__init_model(opts.model, opts.model_opts)
        self.logger.info(self.model)
        self.optimizer = self.__init_optimizer(opts.trainer_opts.optimizer, opts.trainer_opts.optimizer_opts)
        self.logger.info(self.optimizer)
        self.criterion = opts.trainer_opts.criterion(**dc.asdict(opts.trainer_opts.criterion_opts))
        self.logger.info(self.criterion)
        self.data_bunch = opts.data_bunch(opts.data_bunch_opts, opts.data_set_opts, opts.data_loader_opts)
        self.logger.info(self.data_bunch)

        self.metrics = opts.evaluator_opts.metrics
        self.device = th.device('cuda' if th.cuda.is_available() else 'cpu')

        self.trainer, self.evaluator = self.__init_trainer_evaluator()

        self.log_interval = opts.log_interval
        self.iterations = math.ceil(len(self.data_bunch.train_set) / self.data_bunch.dl_opts.batch_size)

        self.__init_handlers()
        self.__init_stats_recorder()

    def __init_record(self, opts: models.RunOptions):
        os.makedirs(ct.RUN_DIR / opts.name, exist_ok=True)
        with open(ct.RUN_DIR / opts.name / 'run.json', 'w') as file:
            json.dump(dc.asdict(opts), file, indent=True, sort_keys=True, default=str)

    def __init_logging(self, run: str):
        logger = logging.getLogger()
        formatter = logging.Formatter('[%(asctime)-s][%(process)d][%(levelname)s]\t%(message)s')
        file_handler = logging.FileHandler(ct.RUN_DIR / run / 'run.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def __init_model(self, model: nn.Module, opts: Any) -> nn.Module:
        model = model(**dc.asdict(opts))
        if self.resume:
            self.logger.info(f'Loading model from {self.resume_from}.')
            model.load_state_dict(th.load(self.resume_from)['model'])

        return model

    def __init_optimizer(self, optimizer: Type[optim.Optimizer], optimizer_opts: Any) -> optim.Optimizer:
        optimizer = optimizer(self.model.parameters(), **dc.asdict(optimizer_opts))
        if self.resume:
            self.logger.info(f'Loading optimizer from {self.resume_from}.')
            optimizer.load_state_dict(th.load(self.resume_from)['optimizer'])

        return optimizer

    def __init_trainer_evaluator(self) -> Tuple[engine.Engine, engine.Engine]:
        trainer = engine.create_supervised_trainer(self.model, self.optimizer, self.criterion, self.device, True)
        if self.resume:
            trainer.state = th.load(self.resume_from)['trainer_state']
        evaluator = engine.create_supervised_evaluator(self.model, self.metrics, self.device, True)
        if self.resume:
            evaluator.state = th.load(self.resume_from)['evaluator_state']

        return trainer, evaluator

    def __init_handlers(self) -> None:
        self.__init_global_timer_handler()
        self.__init_iter_timer_handler()
        self.__init_checkpoint_handler()
        self.trainer.add_event_handler(engine.Events.ITERATION_COMPLETED, self._on_iteration_completed)
        self.trainer.add_event_handler(engine.Events.EPOCH_COMPLETED, self._on_epoch_completed)
        self.trainer.add_event_handler(engine.Events.EXCEPTION_RAISED, self._on_exception_raised)
        self.evaluator.add_event_handler(engine.Events.EXCEPTION_RAISED, self._on_exception_raised)

    def __init_global_timer_handler(self) -> None:
        self.global_timer = handlers.Timer(average=False)
        self.global_timer.attach(self.trainer,
                                 start=engine.Events.STARTED,
                                 step=engine.Events.EPOCH_COMPLETED)

    def __init_iter_timer_handler(self) -> None:
        self.iter_timer = handlers.Timer(average=False)
        self.iter_timer.attach(self.trainer,
                               start=engine.Events.ITERATION_STARTED,
                               step=engine.Events.ITERATION_COMPLETED)

    def __init_checkpoint_handler(self) -> None:
        checkpoint_handler = handlers.ModelCheckpoint(dirname=ct.RUN_DIR / self.name,
                                                      filename_prefix=self.name, n_saved=3,
                                                      save_interval=1, save_as_state_dict=False)
        checkpoint_args = {
            'model': self.model.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'trainer_state': self.trainer.state,
            'evaluator_state': self.evaluator.state
        }
        self.trainer.add_event_handler(engine.Events.EPOCH_COMPLETED, checkpoint_handler, checkpoint_args)

    def __init_stats_recorder(self) -> None:
        fieldnames = ['train_loss', 'valid_loss', 'train_acc@1', 'valid_acc@1', 'train_acc@3', 'valid_acc@3']
        os.makedirs(ct.RUN_DIR / self.name, exist_ok=True)
        self.csv_file = open(ct.RUN_DIR / self.name / 'stats.csv', 'w')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames)
        if not self.resume:
            self.csv_writer.writeheader()

    def _on_iteration_completed(self, _engine: engine.Engine) -> None:
        iteration = (_engine.state.iteration - 1) % len(self.data_bunch.train_set) + 1
        if iteration % self.log_interval == 0:
            self.logger.info(f'[Batch: {_engine.state.iteration:04d}/{self.iterations:4d}]'
                             f'[Iteration Time: {self.iter_timer.value():6.2f}s]'
                             f'[Batch Loss: {_engine.state.output:8.4f}]')

    def _on_epoch_completed(self, _engine: engine.Engine) -> None:
        metrics = {}

        self.evaluator.run(self.data_bunch.train_loader)
        for key, value in self.evaluator.state.metrics.items():
            metrics[f'train_{key}'] = value

        self.evaluator.run(self.data_bunch.valid_loader)
        for key, value in self.evaluator.state.metrics.items():
            metrics[f'valid_{key}'] = value

        self.csv_writer.writerow(metrics)

    def _on_exception_raised(self, _engine: engine.Engine, exception: Exception) -> None:
        self.csv_file.close()

        raise exception

    def run(self) -> None:
        self.trainer.run(self.data_bunch.train_loader, max_epochs=self.epochs)
        self.csv_file.close()