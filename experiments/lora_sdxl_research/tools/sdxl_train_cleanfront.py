"""Clean-front in-context training (CONDITIONING.md option C).  Wraps sd-scripts, does not edit it.

Same as sdxl_train_network.py, except in get_noise_pred_and_target: for each sample, with probability
--clean_front_prob, the FRONT quadrant's latents are left CLEAN (not noised) and that region is
excluded from the loss (its prediction is replaced by the target, so loss and gradient there are 0).
The model learns  p(right, left, back | clean front)  -- exactly the inference task, where the front is
given and stays fixed.  Other samples train the full sheet as usual (keeps the joint distribution).
Box is in LATENT cells: x0,y0,x1,y1 (sheet512: front pixels 16..256 -> latents 2..32).
usage: same args as sdxl_train_network.py plus --clean_front_box 2,2,32,32 --clean_front_prob 0.75"""
import os, random, sys
SD = r'C:\Users\Chris\stardew-lora-lab\sd-scripts'
sys.path.insert(0, SD); os.chdir(SD)
import torch
import sdxl_train_network as S
from library import train_util, args as args_util
from library.utils import setup_logging
import library.custom_train_functions  # noqa: F401  (keeps sd-scripts import order)
try:
    from library import loss_util
except ImportError:                       # older layout
    import library.train_util as loss_util


def front_mask(latents, box, prob, rng=random):
    """(B,1,h,w) float mask: 1 inside the front box for samples chosen with probability prob."""
    x0, y0, x1, y1 = box
    m = torch.zeros_like(latents[:, :1])
    for i in range(latents.shape[0]):
        if rng.random() < prob: m[i, :, y0:y1, x0:x1] = 1.0
    return m


def apply_clean_front(latents, noisy_latents, m):
    return noisy_latents * (1 - m) + latents * m


def mask_prediction(noise_pred, target, m):
    """loss/gradient = 0 where m == 1"""
    return noise_pred * (1 - m) + target.to(noise_pred.dtype).detach() * m


class CleanFrontTrainer(S.SdxlNetworkTrainer):
    def get_noise_pred_and_target(self, args, accelerator, noise_scheduler, latents, batch, text_encoder_conds, unet,
                                  network, weight_dtype, train_unet, is_train=True):
        noise, noisy_latents, timesteps = loss_util.get_noise_noisy_latents_and_timesteps(args, noise_scheduler, latents)
        box = [int(v) for v in args.clean_front_box.split(',')]
        m = front_mask(latents, box, args.clean_front_prob if is_train else 1.0).to(noisy_latents.dtype)
        noisy_latents = apply_clean_front(latents.to(noisy_latents.dtype), noisy_latents, m)
        if args.gradient_checkpointing:
            for x in noisy_latents: x.requires_grad_(True)
            for t in text_encoder_conds: t.requires_grad_(True)
        with torch.set_grad_enabled(is_train), accelerator.autocast():
            noise_pred = self.call_unet(args, accelerator, unet, noisy_latents.requires_grad_(train_unet), timesteps,
                                        text_encoder_conds, batch, weight_dtype)
        target = noise_scheduler.get_velocity(latents, noise, timesteps) if args.v_parameterization else noise
        noise_pred = mask_prediction(noise_pred, target, m.to(noise_pred.dtype))
        return noise_pred, target, timesteps, None


def setup_parser():
    p = S.setup_parser()
    p.add_argument('--clean_front_box', type=str, default='2,2,32,32')
    p.add_argument('--clean_front_prob', type=float, default=0.75)
    return p


def cap_vram():
    """CLEANFRONT_VRAM_MB: cap on the WHOLE GPU's use (nvidia-smi view).  Try 1 (2026-10-12) sat at 5973 of
    6144 MiB and the laptop froze; a capped allocator raises OOM instead of spilling into shared memory.
    mem_get_info creates this process's CUDA context first, so 'in use' = desktop + our context (neither is
    counted by the allocator); allocator budget = cap - in use."""
    mb = int(os.environ.get('CLEANFRONT_VRAM_MB', '0'))
    if not mb or not torch.cuda.is_available(): return
    free, total = torch.cuda.mem_get_info(); used = (total - free) / 2**20
    frac = max(0.5, (mb - used) / (total / 2**20))
    torch.cuda.set_per_process_memory_fraction(frac)
    print(f'[cleanfront] VRAM cap {mb} MiB: in use {used:.0f} MiB, allocator fraction {frac:.3f}', flush=True)


if __name__ == '__main__':
    setup_logging()
    cap_vram()
    parser = setup_parser(); args = parser.parse_args()
    args_util.verify_command_line_training_args(args)
    args = args_util.read_config_from_file(args, parser)
    CleanFrontTrainer().train(args)
