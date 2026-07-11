from enum import Enum


class ProgressStage(Enum):
    PREPARING = "preparing"
    LOADING_VERSION = "loading_version"

    DOWNLOADING_CLIENT = "downloading_client"
    DOWNLOADING_LIBRARIES = "downloading_libraries"
    DOWNLOADING_ASSET_INDEX = "downloading_asset_index"
    DOWNLOADING_ASSETS = "downloading_assets"

    BUILDING_CONTEXT = "building_context"
    BUILDING_COMMAND = "building_command"

    SELECTING_JAVA = "selecting_java"
    LAUNCHING = "launching"
    FINISHED = "finished"