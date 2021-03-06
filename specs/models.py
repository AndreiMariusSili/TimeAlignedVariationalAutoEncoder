import options.model_options as mo

########################################################################################################################
# TimeAlignedDenseNet
########################################################################################################################
tadn_class_4 = mo.TADNModel(
    opts=mo.TADNOptions(
        batch_size=32,
        time_steps=4,
        temporal_in_planes=64,
        growth_rate=64,
        temporal_drop_rate=0.0,
        classifier_drop_rate=0.5,
        class_embed_planes=512
    )
)
tadn_class_8 = mo.TADNModel(
    opts=mo.TADNOptions(
        batch_size=8,
        time_steps=8,
        temporal_in_planes=64,
        growth_rate=64,
        temporal_drop_rate=0.0,
        classifier_drop_rate=0.5,
        class_embed_planes=512
    )
)
########################################################################################################################
# TimeAlignedResNet
########################################################################################################################
tarn_class_4 = mo.TARNModel(
    opts=mo.TARNOptions(
        batch_size=32,
        time_steps=4,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        classifier_drop_rate=0.5,
        class_embed_planes=512,
    )
)
tarn_class_8 = mo.TARNModel(
    opts=mo.TARNOptions(
        batch_size=16,
        time_steps=8,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        classifier_drop_rate=0.5,
        class_embed_planes=512,
    )
)
tarn_ae_4 = mo.AETARNModel(
    opts=mo.AETARNOptions(
        batch_size=32,
        time_steps=4,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        spatial_decoder_planes=[256, 128, 64, 32, 16],
        classifier_drop_rate=0.5,
        flow=False,
        class_embed_planes=512,
    )
)
tarn_flow_4 = mo.AETARNModel(
    opts=mo.AETARNOptions(
        batch_size=32,
        time_steps=4,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        spatial_decoder_planes=[256, 128, 64, 32, 16],
        classifier_drop_rate=0.5,
        flow=True,
        class_embed_planes=512,
    )
)
tarn_gsnn_4 = mo.GSNNTARNModel(
    opts=mo.GSNNTARNOptions(
        batch_size=16,
        time_steps=4,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        classifier_drop_rate=0.5,
        class_embed_planes=512,
        vote_type='soft',
    )
)
tarn_vae_4 = mo.VAETARNModel(
    opts=mo.VAETARNOptions(
        batch_size=16,
        time_steps=4,
        spatial_encoder_planes=[16, 32, 64, 128, 256],
        bottleneck_planes=64,
        spatial_decoder_planes=[64, 64, 64, 64, 64],
        classifier_drop_rate=0.5,
        class_embed_planes=512,
        vote_type='soft',
    )
)
########################################################################################################################
# I3D
########################################################################################################################
i3d_class_4 = mo.I3DModel(
    opts=mo.I3DOptions(
        batch_size=32,
        time_steps=4,
        dropout_prob=0.5,
    )
)
i3d_class_8 = mo.I3DModel(
    opts=mo.I3DOptions(
        batch_size=8,
        time_steps=8,
        dropout_prob=0.5,
    )
)
i3d_ae_4 = mo.AEI3DModel(
    opts=mo.AEI3DOptions(
        batch_size=8,
        time_steps=4,
        embed_planes=1024,
        dropout_prob=0.5,
        flow=False,
    )
)
i3d_flow_4 = mo.AEI3DModel(
    opts=mo.AEI3DOptions(
        batch_size=8,
        time_steps=4,
        embed_planes=1024,
        dropout_prob=0.5,
        flow=True,
    )
)
i3d_ae_8 = mo.AEI3DModel(
    opts=mo.AEI3DOptions(
        batch_size=4,
        time_steps=8,
        embed_planes=1024,
        dropout_prob=0.5,
        flow=False,
    )
)
i3d_gsnn_4 = mo.GSNNI3DModel(
    opts=mo.GSNNI3DOptions(
        batch_size=8,
        time_steps=4,
        latent_planes=1024,
        dropout_prob=0.5,
        vote_type='soft'
    )
)
i3d_vae_4 = mo.VAEI3DModel(
    opts=mo.VAEI3DOptions(
        batch_size=8,
        time_steps=4,
        latent_planes=1024,
        dropout_prob=0.5,
        vote_type='soft'
    )
)
