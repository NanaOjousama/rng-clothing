"""Unit test for the clean-front patch (CPU, no model, no training)."""
import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import sdxl_train_cleanfront as C
torch.manual_seed(0); rng = random.Random(1)
lat = torch.randn(4, 4, 64, 64); noise = torch.randn_like(lat); noisy = lat + 3 * noise
box = (2, 2, 32, 32)
m = C.front_mask(lat, box, 1.0, rng)
assert m.shape == (4, 1, 64, 64) and m.sum().item() == 4 * 30 * 30, 'mask covers exactly the front box'
mixed = C.apply_clean_front(lat, noisy, m)
assert torch.equal(mixed[:, :, 2:32, 2:32], lat[:, :, 2:32, 2:32]), 'front region clean'
assert torch.equal(mixed[:, :, 40:, 40:], noisy[:, :, 40:, 40:]), 'other quadrants still noised'
pred = torch.randn_like(lat, requires_grad=True)
out = C.mask_prediction(pred, noise, m)
loss = torch.nn.functional.mse_loss(out, noise); loss.backward()
g = pred.grad
assert g[:, :, 2:32, 2:32].abs().max().item() == 0, 'no gradient from the front region'
assert g[:, :, 40:, 40:].abs().max().item() > 0, 'gradient flows from the other quadrants'
m0 = C.front_mask(lat, box, 0.0, rng); assert m0.sum().item() == 0, 'prob 0 -> plain training'
mh = C.front_mask(torch.randn(2000, 4, 8, 8), (0, 0, 4, 4), 0.75, random.Random(5))
frac = (mh[:, 0, 0, 0] > 0).float().mean().item(); assert 0.72 < frac < 0.78, f'prob 0.75 honoured ({frac:.3f})'
print('ALL CLEAN-FRONT TESTS PASS', f'(prob check {frac:.3f})')
