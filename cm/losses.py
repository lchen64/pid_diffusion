"""
Helpers for various likelihood-based losses. These are ported from the original
Ho et al. diffusion models codebase:
https://github.com/hojonathanho/diffusion/blob/1e0dceb3b3495bbe19116a5e1b3596cd0706c543/diffusion_tf/utils.py
"""

import numpy as np
import torch as th


def normal_kl(mean1, logvar1, mean2, logvar2):
    """
    Compute the KL divergence between two gaussians.

    Shapes are automatically broadcasted, so batches can be compared to
    scalars, among other use cases.
    """
    tensor = None
    for obj in (mean1, logvar1, mean2, logvar2):
        if isinstance(obj, th.Tensor):
            tensor = obj
            break
    assert tensor is not None, "at least one argument must be a Tensor"

    # Force variances to be Tensors. Broadcasting helps convert scalars to
    # Tensors, but it does not work for th.exp().
    logvar1, logvar2 = [
        x if isinstance(x, th.Tensor) else th.tensor(x).to(tensor)
        for x in (logvar1, logvar2)
    ]

    return 0.5 * (
        -1.0
        + logvar2
        - logvar1
        + th.exp(logvar1 - logvar2)
        + ((mean1 - mean2) ** 2) * th.exp(-logvar2)
    )


def approx_standard_normal_cdf(x):
    """
    A fast approximation of the cumulative distribution function of the
    standard normal.
    """
    return 0.5 * (1.0 + th.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * th.pow(x, 3))))


def discretized_gaussian_log_likelihood(x, *, means, log_scales):
    """
    Compute the log-likelihood of a Gaussian distribution discretizing to a
    given image.

    :param x: the target images. It is assumed that this was uint8 values,
              rescaled to the range [-1, 1].
    :param means: the Gaussian mean Tensor.
    :param log_scales: the Gaussian log stddev Tensor.
    :return: a tensor like x of log probabilities (in nats).
    """
    assert x.shape == means.shape == log_scales.shape
    centered_x = x - means
    inv_stdv = th.exp(-log_scales)
    plus_in = inv_stdv * (centered_x + 1.0 / 255.0)
    cdf_plus = approx_standard_normal_cdf(plus_in)
    min_in = inv_stdv * (centered_x - 1.0 / 255.0)
    cdf_min = approx_standard_normal_cdf(min_in)
    log_cdf_plus = th.log(cdf_plus.clamp(min=1e-12))
    log_one_minus_cdf_min = th.log((1.0 - cdf_min).clamp(min=1e-12))
    cdf_delta = cdf_plus - cdf_min
    log_probs = th.where(
        x < -0.999,
        log_cdf_plus,
        th.where(x > 0.999, log_one_minus_cdf_min, th.log(cdf_delta.clamp(min=1e-12))),
    )
    assert log_probs.shape == x.shape
    return log_probs


def gaussian_ecfd(X, Y, sigmas, num_freqs=8, optimize_sigma=False):
    """Computes ECFD with Gaussian weighting distribution.
    
    Arguments:
        X {torch.Tensor} -- Samples from distribution P of shape [B x D].
        Y {torch.Tensor} -- Samples from distribution Q of shape [B x D].
        sigmas {list} or {torch.Tensor} -- A list of floats or a torch Tensor of
                                           shape [1 x D] if optimize_sigma is True.
    
    Keyword Arguments:
        num_freqs {int} -- Number of random frequencies to use (default: {8}).
        optimize_sigma {bool} -- Whether to optimize sigma (default: {False}).
    
    Returns:
        torch.Tensor -- The ECFD.
    """    
    total_loss = 0.0
    if not optimize_sigma:
        for sigma in sigmas:
            batch_loss = _gaussian_ecfd(X, Y, sigma, num_freqs=num_freqs)
            total_loss += batch_loss
    else:
        batch_loss = _gaussian_ecfd(X, Y, sigmas, num_freqs=num_freqs)
        total_loss += batch_loss / th.norm(sigmas, p=2)
    return total_loss

def _gaussian_ecfd(X, Y, sigma, num_freqs=8):
    wX, wY = 1.0, 1.0
    X, Y = X.view(X.size(0), -1), Y.view(Y.size(0), -1)
    batch_size, dim = X.size()
    t = (th.randn((num_freqs, dim)).cuda()).to(dtype=th.long, device='cuda') * sigma
    X_reshaped = X.view((batch_size, dim))
    tX = th.matmul(t, X_reshaped.t())
    cos_tX = (th.cos(tX) * wX).mean(1)
    sin_tX = (th.sin(tX) * wX).mean(1)
    Y_reshaped = Y.view((batch_size, dim))
    tY = th.matmul(t, Y_reshaped.t())
    cos_tY = (th.cos(tY) * wY).mean(1)
    sin_tY = (th.sin(tY) * wY).mean(1)
    loss = (cos_tX - cos_tY) ** 2 + (sin_tX - sin_tY) ** 2
    return loss.mean()


def uniform_ecfd(X, Y, sigmas, num_freqs=8, optimize_sigma=False):
    """Computes ECFD with Uniform weighting distribution [-sigma, sigma].
    
    Arguments:
        X {torch.Tensor} -- Samples from distribution P of shape [B x D].
        Y {torch.Tensor} -- Samples from distribution Q of shape [B x D].
        sigmas {list} or {torch.Tensor} -- A list of floats or a torch Tensor of
                                           shape [1 x D] if optimize_sigma is True.
    
    Keyword Arguments:
        num_freqs {int} -- Number of random frequencies to use (default: {8}).
        optimize_sigma {bool} -- Whether to optimize sigma (default: {False}).
    
    Returns:
        torch.Tensor -- The ECFD.
    """  
    total_loss = 0.0
    if not optimize_sigma:
        for sigma in sigmas:
            batch_loss = _uniform_ecfd(X, Y, sigma, num_freqs=num_freqs)
            total_loss += batch_loss
    else:
        batch_loss = _uniform_ecfd(X, Y, sigmas, num_freqs=num_freqs)
        total_loss += batch_loss / torch.norm(sigmas, p=2)
    return total_loss


def _uniform_ecfd(X, Y, sigma, num_freqs=8):
    X, Y = X.view(X.size(0), -1), Y.view(Y.size(0), -1)
    batch_size, dim = X.size()
    t = (2 * torch.rand((num_freqs, dim)).cuda() - 1.0) * sigma
    X_reshaped = X.view((batch_size, dim))
    tX = torch.matmul(t, X_reshaped.t())
    cos_tX = torch.cos(tX).mean(1)
    sin_tX = torch.sin(tX).mean(1)
    Y_reshaped = Y.view((batch_size, dim))
    tY = torch.matmul(t, Y_reshaped.t())
    cos_tY = torch.cos(tY).mean(1)
    sin_tY = torch.sin(tY).mean(1)
    loss = (cos_tX - cos_tY) ** 2 + (sin_tX - sin_tY) ** 2
    return loss.mean()