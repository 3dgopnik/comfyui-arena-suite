# __init__.py for F:\ComfyUI\ComfyUI\custom_nodes\ComfyUI_Arena

from .arena_make_tiles_segs import Arena_MakeTilesSegs

# Register the node in ComfyUI
NODE_CLASS_MAPPINGS = {
    "Arena_MakeTilesSegs": Arena_MakeTilesSegs
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Arena_MakeTilesSegs": "Arena Make Tiles Segments"
}
