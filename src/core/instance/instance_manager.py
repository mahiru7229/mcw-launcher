from src.models.minecraft.version import Version
from src.models.instance.instance import Instance
from pathlib import Path
from src.core.fs.paths import Paths
import json
import shutil


class InstanceManager:
    @staticmethod
    def load(name:str, version:Version, mod_loader=("vanilla", "-1")) -> Instance:
        Paths.instances_root()
        if not Path(Paths.instances_root() / "instances.json").exists():
            Paths.instance_data_path_create()
        if not InstanceManager._is_instance_exist(name):
            InstanceManager._create(name,version,mod_loader)
        instances_data = InstanceManager._load_instances_data()
        instances = InstanceManager._parse_instances(instances_data)
        for instance in instances:
            print(instance)
            if instance.name == name:
                return instance
        raise RuntimeError("No instance has been loaded.")
    
    @staticmethod
    def delete_instance(name:str) -> bool:
        Paths.instances_root()
        if not Path(Paths.instances_root() / "instances.json").exists():
            Paths.instance_data_path_create()
        instances_data = InstanceManager._load_instances_data()
        original_count = len(instances_data["instances"])
        instances_data["instances"] = [
            inst for inst in instances_data["instances"] 
            if inst.get("name") != name
        ]
        if (len(instances_data["instances"]) < original_count):
            instance_dir = Paths.load_instance_dir(name)
            if instance_dir.exists():
                shutil.rmtree(instance_dir)
            InstanceManager._save_instances(instances_data)
            return True
        
        return False



    @staticmethod
    def _create(name:str, version:Version, mod_loader) -> Path:
        instance = InstanceManager._add_instance(name, version, mod_loader)
        instance_data = InstanceManager._add_instances_data(InstanceManager._load_instances_data(),instance)
        InstanceManager._save_instances(instance_data)

    @staticmethod
    def _is_instance_exist(name:str)->bool:
        instances_data = InstanceManager._load_instances_data()
        for instance in instances_data["instances"]:
            if instance.get("name") == name:
                return True
        return False
    @staticmethod
    def _add_instance(name:str, version:Version, mod_loader:tuple) -> Instance:
        return Instance(
            name = name,
            version_id=version.id,
            instance_dir = Paths.load_instance_dir(name),
            mod_loader=mod_loader
        )

    @staticmethod
    def _save_instances(data:dict) -> dict:
        instance_data_path = Paths.instance_data_path()
        instance_data_path.write_text(json.dumps(data, indent=4),encoding="utf-8")
        return instance_data_path


    @staticmethod
    def _add_instances_data(pre_data:dict, instance_data:Instance) -> dict:
        if "instances" not in pre_data:
            pre_data["instances"] = []
        data = pre_data
        data["instances"].append({
                "name" :instance_data.name,
                "version_id" : instance_data.version_id,
                "instance_dir": str(instance_data.instance_dir),
                "mod_loader": instance_data.mod_loader  
            }
        )
        return data
    @staticmethod
    def _load_instances_data() -> dict:
        try:
            return json.loads(Paths.instance_data_path().read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"instances": []}
    @staticmethod 
    def _parse_instances(instances_data: dict) -> list[Instance]:
        instances: list[Instance] = []
        for instance_dict in instances_data.get("instances", []):
            instances.append(
                Instance(
                    name=instance_dict.get("name"),
                    version_id=instance_dict.get("version_id"), 
                    instance_dir=instance_dict.get("instance_dir"), 
                    mod_loader=instance_dict.get("mod_loader")
                )
            )
        return instances
    

        



    