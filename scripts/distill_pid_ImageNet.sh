
# PID on ImageNet 64x64
module purge
module load cuda/12.4 ompi/5.0.1-it
export devices="auto"

OPENAI_LOGDIR=./experiment/pid_imagenet python cm_train.py \
     --training_mode one_shot_pinn_edm_edm \
     --target_ema_mode fixed \
     --start_ema 0.5 \
     --scale_mode fixed \
     --start_scales 250 \
     --total_training_steps 5000 \
     --loss_norm lpips \
     --lr_anneal_steps 0 \
     --teacher_model_path model_zoo/edm-imagenet-64x64-cond-adm.ckpt \
     --attention_resolutions "2" \
     --class_cond True \
     --use_scale_shift_norm True \
     --dropout 0.0 \
     --teacher_dropout 0.0 \
     --ema_rate 0.999,0.9999,0.99995 \
     --global_batch_size 9 \
     --image_size 64 \
     --lr 0.0001 \
     --num_channels 192 \
     --num_res_blocks 3 \
     --resblock_updown True \
     --schedule_sampler uniform \
     --use_fp16 True \
     --weight_decay 0.0 \
     --weight_schedule uniform \
     --optimizer radam
