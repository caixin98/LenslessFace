import torch
pretrain_ckpt = "/mnt/data/oss_beijing/caixin/t2t-vit-t-14_3rdparty_8xb64_in1k_20210928-b7c09b62.pth"
optical = dict(
    type='SoftPsfConv',
    feature_size=2.76e-05,
    sensor='IMX250',
    input_shape=[3, 308, 257],
    scene2mask=0.4,
    mask2sensor=0.002,
    target_dim=[224, 187],
    requires_grad=True,
    use_stn=False,
    do_optical=False,
    down="resize",
    noise_type=None,
    do_affine=True,
    n_psf_mask=1)
propagated_args = dict(
    mask2sensor=0.002,
    scene2mask=0.4,
    object_height=0.27,
    sensor='IMX250',
    single_psf=False,
    grayscale=False,
    input_dim=[112, 96, 3],
    output_dim=[308, 257, 3],
    dtype_out=torch.float32)
find_unused_parameters = True
log_config = dict(interval=100, hooks=[dict(type='TextLoggerHook')])
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
img_norm_cfg = dict(
    mean=[127.5, 127.5, 127.5], std=[128.0, 128.0, 128.0], to_rgb=True)


data = dict(
    workers_per_gpu=2,
    train=dict(
        type='AffectNet',
        img_prefix='data/OrderAffectNet/train/',
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='Resize', size=(256, 256)),
            dict(type='RandomFlip', flip_prob=0.5, direction='horizontal'),
            dict(
                type='Propagated',
                mask2sensor=0.002,
                scene2mask=0.4,
                object_height=0.27,
                sensor='IMX250',
                single_psf=False,
                grayscale=False,
                input_dim=[256, 256, 3],
                output_dim=[256, 256, 3],
                dtype_out=torch.float32),
            dict(
                    type='TorchAffineRTS',
                    angle=(0, 0),
                    prob=0.0,
                ),
            dict(type='ToTensor', keys=['gt_label']),
             dict(type='StackImagePair', keys=['img_nopad'], out_key='img'),
            dict(type='Collect', keys=['img','gt_label', 'affine_matrix'])
        ]),
    val=dict(
        type='AffectNet',
        img_prefix='data/OrderAffectNet/val/',
        # test_mode=False,
        test_mode=True,
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='Resize', size=(256, 256)),
            dict(type='RandomFlip', flip_prob=0.5, direction='horizontal'),
            dict(
                type='Propagated',
                mask2sensor=0.002,
                scene2mask=0.4,
                object_height=0.27,
                sensor='IMX250',
                single_psf=False,
                grayscale=False,
                input_dim=[256, 256, 3],
                output_dim=[256, 256, 3],
                dtype_out=torch.float32),
            dict(
                    type='TorchAffineRTS',
                    angle=(0, 0),
                    prob=0.0,
                ),
            dict(type='ToTensor', keys=['gt_label']),
             dict(type='StackImagePair', keys=['img_nopad'], out_key='img'),
            dict(type='Collect', keys=['img','gt_label', 'affine_matrix'])
        ]),
    train_dataloader=dict(samples_per_gpu=48),
    val_dataloader=dict(samples_per_gpu=32),
    test_dataloader=dict(samples_per_gpu=32))
# custom_hooks = [
#     dict(type='VisualConvHook'),
#     dict(type='VisualAfterOpticalHook')
# ]

# model = dict(
#     type='AffineFaceImageClassifier',
#     backbone=dict(
#         type='ResNet',
#         depth=18,
#         num_stages=4,
#         out_indices=(3, ),
#         style='pytorch'),
#     neck=dict(type='GlobalAveragePooling'),
#     head=dict(
#         type='LinearClsHead',
#         num_classes=7,
#         in_channels=512,
#         loss=dict(type='CrossEntropyLoss', loss_weight=1.0),
#         topk=(1, ),
#     ))
num_classes = 7
embed_dims = 384
model = dict(
    type='AffineFaceImageClassifier',
    backbone=dict(
        type='T2T_ViT_optical',
        optical=optical,
        apply_affine=True,
        output_cls_token=True,
        image_size=224,
        in_channels=3,
        embed_dims=embed_dims,
        t2t_cfg=dict(
            token_dims=64,
            use_performer=False,
        ),
        num_layers=14,
        layer_cfgs=dict(
            num_heads=6,
            feedforward_channels=3 * embed_dims,  # mlp_ratio = 3
        ),
        drop_path_rate=0.1,
        init_cfg=[
            dict(type='TruncNormal', layer='Linear', std=.02),
            dict(type='Constant', layer='LayerNorm', val=1., bias=0.),
        ]),
    neck=None,
    head=dict(
        type='VisionTransformerClsHead',
        num_classes=num_classes,
        in_channels=embed_dims,
        loss=dict(
            type='LabelSmoothLoss',
            label_smooth_val=0.1,
            mode='original',
        ),
        topk=(1, ),
        init_cfg=dict(type='TruncNormal', layer='Linear', std=.02)),
    init_cfg=dict(type='Pretrained', checkpoint=pretrain_ckpt,)
)
    
optimizer = dict(type='AdamW',lr=2e-5, weight_decay=0.05)
lr_config = dict(
    policy='CosineAnnealingCooldown',
    min_lr=1e-7,
    cool_down_time=10,
    cool_down_ratio=0.1,
    by_epoch=True,
    warmup_by_epoch=True,
    warmup='linear',
    warmup_iters=20,
    warmup_ratio=1e-6)
checkpoint_config = dict(interval=10)
runner = dict(type='EpochBasedRunner', max_epochs=100)
evaluation = dict(interval=1, metric='accuracy')
# runner = dict(type='IterBasedRunner', max_iters=200000)
# checkpoint_config = dict(interval=1000)
# evaluation = dict(interval=500,metric='accuracy')
optimizer_config = dict(grad_clip=dict(max_norm=1, norm_type=2))
