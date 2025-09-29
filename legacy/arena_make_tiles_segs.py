import logging
import math

import numpy as np
import torch

from . import IMPACT_AVAILABLE, IMPACT_MISSING_MESSAGE


LOGGER = logging.getLogger(__name__)

if IMPACT_AVAILABLE:
    from impact.core import SEG  # type: ignore  # Import SEG class
    from impact.utils import *  # type: ignore  # Import all utility functions

    from . import core  # Import core module for mask operations
else:
    SEG = None  # type: ignore
    core = None  # type: ignore
    LOGGER.warning(IMPACT_MISSING_MESSAGE)

class Arena_MakeTilesSegs:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "crop_factor": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 10, "step": 0.01}),
                "min_overlap": ("INT", {"default": 5, "min": 0, "max": 512, "step": 1}),
                "filter_segs_dilation": ("INT", {"default": 20, "min": -255, "max": 255, "step": 1}),
                "mask_irregularity": ("FLOAT", {"default": 0, "min": 0, "max": 1.0, "step": 0.01}),
                "irregular_mask_mode": (["Reuse fast", "Reuse quality", "All random fast", "All random quality"],)
            },
            "optional": {
                "filter_in_segs_opt": ("SEGS",),
                "filter_out_segs_opt": ("SEGS",)
            }
        }

    RETURN_TYPES = ("SEGS",)
    FUNCTION = "doit"
    CATEGORY = "Arena/Tiles"

    @staticmethod
    def doit(images, width, height, crop_factor, min_overlap, filter_segs_dilation, mask_irregularity=0, irregular_mask_mode="Reuse fast", filter_in_segs_opt=None, filter_out_segs_opt=None):
        if not IMPACT_AVAILABLE:
            raise RuntimeError(IMPACT_MISSING_MESSAGE)

        # Ensure that min_overlap is less than half the width and height
        if width <= 2 * min_overlap:
            min_overlap = width / 2
        if height <= 2 * min_overlap:
            min_overlap = height / 2

        _, ih, iw, _ = images.size()

        # Initialize mask cache and set default mask quality
        mask_cache = None
        mask_quality = 512

        # Handle irregular mask mode based on mask_irregularity value
        if mask_irregularity > 0:
            if irregular_mask_mode == "Reuse fast":
                mask_quality = 128
                mask_cache = np.zeros((128, 128), dtype=np.float32)
                core.random_mask(mask_cache, (0, 0, 128, 128), factor=mask_irregularity, size=mask_quality)
            elif irregular_mask_mode == "Reuse quality":
                mask_quality = 512
                mask_cache = np.zeros((512, 512), dtype=np.float32)
                core.random_mask(mask_cache, (0, 0, 512, 512), factor=mask_irregularity, size=mask_quality)
            elif irregular_mask_mode in ["All random fast", "All random quality"]:
                mask_quality = 512

        # Adjust the overlap based on mask_irregularity
        if mask_irregularity > 0:
            compensate = max(6, int(mask_quality * mask_irregularity / 4))
            min_overlap += compensate
            width += compensate * 2
            height += compensate * 2

        # Handle exclusion mask processing
        exclusion_mask = None
        if filter_out_segs_opt is not None:
            exclusion_mask = core.segs_to_combined_mask(filter_out_segs_opt)
            exclusion_mask = make_3d_mask(exclusion_mask)
            exclusion_mask = resize_mask(exclusion_mask, (ih, iw))
            exclusion_mask = dilate_mask(exclusion_mask.cpu().numpy(), filter_segs_dilation)

        # Process inclusion mask if provided
        and_mask = None
        start_x = start_y = 0
        w, h = iw, ih
        if filter_in_segs_opt is not None:
            and_mask = core.segs_to_combined_mask(filter_in_segs_opt)
            and_mask = make_3d_mask(and_mask)
            and_mask = resize_mask(and_mask, (ih, iw))
            and_mask = dilate_mask(and_mask.cpu().numpy(), filter_segs_dilation)

            a, b = core.mask_to_segs(and_mask, True, 1.0, False, 0)
            if len(b) > 0:
                start_x, start_y, c, d = b[0].crop_region
                w, h = c - start_x, d - start_y

        # Adjust width and height to fit within bounds
        if width > w or height > h:
            width = min(width, w)
            height = min(height, h)

        # Calculate number of tiles and overlaps
        n_horizontal = math.ceil(w / (width - min_overlap))
        n_vertical = math.ceil(h / (height - min_overlap))

        w_overlap_sum = (width * n_horizontal) - w
        if w_overlap_sum < 0:
            n_horizontal += 1
            w_overlap_sum = (width * n_horizontal) - w

        w_overlap_size = 0 if n_horizontal == 1 else int(w_overlap_sum / (n_horizontal - 1))

        h_overlap_sum = (height * n_vertical) - h
        if h_overlap_sum < 0:
            n_vertical += 1
            h_overlap_sum = (height * n_vertical) - h

        h_overlap_size = 0 if n_vertical == 1 else int(h_overlap_sum / (n_vertical - 1))

        new_segs = []

        y = start_y
        for j in range(n_vertical):
            x = start_x
            for i in range(n_horizontal):
                x1 = x
                y1 = y
                x2 = min(x + width, iw)
                y2 = min(y + height, ih)

                bbox = (x1, y1, x2, y2)
                crop_region = core.make_crop_region(iw, ih, bbox, crop_factor)
                cx1, cy1, cx2, cy2 = crop_region

                mask = np.zeros((cy2 - cy1, cx2 - cx1), dtype=np.float32)

                rel_left = x1 - cx1
                rel_top = y1 - cy1
                rel_right = x2 - cx1
                rel_bot = y2 - cy1

                # Apply mask irregularity logic if required
                if mask_irregularity > 0:
                    if mask_cache is not None:
                        core.adaptive_mask_paste(mask, mask_cache, (rel_left, rel_top, rel_right, rel_bot))
                    else:
                        core.random_mask(mask, (rel_left, rel_top, rel_right, rel_bot), factor=mask_irregularity, size=mask_quality)

                    # Corner filling
                    if rel_left == 0:
                        pad = int((x2 - x1) / 8)
                        mask[rel_top:rel_bot, :pad] = 1.0

                    if rel_top == 0:
                        pad = int((y2 - y1) / 8)
                        mask[:pad, rel_left:rel_right] = 1.0

                    if rel_right == mask.shape[1]:
                        pad = int((x2 - x1) / 8)
                        mask[rel_top:rel_bot, -pad:] = 1.0

                    if rel_bot == mask.shape[0]:
                        pad = int((y2 - y1) / 8)
                        mask[-pad:, rel_left:rel_right] = 1.0
                else:
                    mask[rel_top:rel_bot, rel_left:rel_right] = 1.0

                if exclusion_mask is not None:
                    exclusion_mask_cropped = exclusion_mask[cy1:cy2, cx1:cx2]
                    mask[exclusion_mask_cropped != 0] = 0.0

                if and_mask is not None:
                    and_mask_cropped = and_mask[cy1:cy2, cx1:cx2]
                    mask[and_mask_cropped == 0] = 0.0

                is_mask_zero = torch.all(torch.tensor(mask) == 0.0).item()

                if not is_mask_zero:
                    new_segs.append(SEG(None, mask, 1.0, crop_region, bbox, "", None))

                x += width - w_overlap_size
            y += height - h_overlap_size

        return ((ih, iw), new_segs),

# Register node for ComfyUI
NODE_CLASS_MAPPINGS = {
    "Arena_MakeTilesSegs": Arena_MakeTilesSegs
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Arena_MakeTilesSegs": "🅰️ Arena Make Tiles Segments"
}
