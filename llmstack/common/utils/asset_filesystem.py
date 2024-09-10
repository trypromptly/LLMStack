import fsspec


def file_extension_to_mime_type(file_name):
    """
    Convert a file extension to a MIME type.
    """
    from mimetypes import guess_type

    return guess_type(f"{file_name}")[0]


class AssetFileSystem(fsspec.AbstractFileSystem):
    def __init__(self, *args, **kwargs):
        self._username = kwargs.pop("username", None)
        self._app_uuid = kwargs.pop("app_uuid", None)

        if not self._username:
            raise ValueError("Username is required")

        super().__init__(*args, **kwargs)

    def _parse_path(self, path):
        if not path:
            raise ValueError("Path cannot be empty")

        category = path.split("/")[0]
        if category not in ["sessionfiles", "appdata"]:
            raise ValueError(f"Invalid category: {category}")
        ref_id = path.split("/")[1]
        file_path = "/".join(path.split("/")[2:]) if len(path.split("/")) > 2 else None
        return category, ref_id, file_path

    def _get_model_cls(self, category):
        from llmstack.apps.models import AppDataAssets, AppSessionFiles

        if category == "sessionfiles":
            return AppSessionFiles
        elif category == "appdata":
            return AppDataAssets
        else:
            return None

    def _get_model_instance_metadata(self, category):
        if category == "sessionfiles" or category == "appdata":
            return {"app_uuid": self._app_uuid, "username": self._username}

    def _get_all_assets(self, category, ref_id):
        model_cls = self._get_model_cls(category)
        assets = model_cls.objects.all().filter(ref_id=ref_id)
        assets = [asset for asset in assets if asset.metadata.get("username") == self._username]
        assets = [asset for asset in assets if "/" in asset.metadata.get("file_name")]
        return assets

    def touch(self, path, truncate=True, **kwargs):
        category, ref_id, file_path = self._parse_path(path)
        if not file_path:
            raise ValueError("Operation not permitted at the root level")
        model_cls = self._get_model_cls(category)
        assets = self._get_all_assets(category=category, ref_id=ref_id)
        for asset in assets:
            if asset.metadata.get("file_name", "") == file_path:
                if truncate:
                    asset.file.truncate(0)
                return True
        mime_type = file_extension_to_mime_type(file_path) or "application/octet-stream"
        asset = model_cls.create_from_bytes(
            b"",
            file_path,
            {
                "file_name": file_path,
                "file_size": 0,
                "mime_type": mime_type,
                **self._get_model_instance_metadata(category),
            },
            ref_id=ref_id,
        )
        return True

    def open(self, path, mode="rb", **kwargs):
        category, ref_id, file_path = self._parse_path(path)
        if not file_path:
            raise ValueError("Operation not permitted at the root level")
        assets = self._get_all_assets(category=category, ref_id=ref_id)
        for asset in assets:
            if asset.metadata.get("file_name", "") == file_path:
                return asset.file.open(mode)

        if "r" in mode:
            raise FileNotFoundError(f"File not found: {file_path}")
        # If file not found, we need create a empty file and return its file object
        if "w" in mode or "a" in mode:
            self.touch(path)
            return self.open(path, mode)
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def rm(self, path):
        """
        Remove a file associated with an Assets instance.
        """
        category, ref_id, file_path = self._parse_path(path)
        if not file_path:
            raise ValueError("Operation not permitted at the root level")
        assets = self._get_all_assets(category=category, ref_id=ref_id)
        asset_to_delete = None
        for asset in assets:
            if asset.metadata.get("file_name", "") == file_path:
                asset_to_delete = asset
                break
        if asset_to_delete:
            asset_to_delete.delete()
            return True
        return False

    def ls(self, path=None, detail=False, **kwargs):
        """
        List all files (represented by Assets) and their metadata.
        The `path` is ignored as we're listing all assets in the database.
        """
        category, ref_id, file_path = self._parse_path(path)
        assets = self._get_all_assets(category=category, ref_id=ref_id)
        files_list = []

        for asset in assets:
            if file_path and not asset.metadata.get("file_name", "").startswith(file_path):
                continue
            file_info = {
                "name": asset.metadata.get("file_name", ""),
                "size": asset.metadata.get("file_size", 0),
                "created_at": asset.created_at,
                "file_name": asset.metadata.get("file_name", ""),
            }
            files_list.append(file_info)

        if detail:
            return files_list
        return [file_info["name"] for file_info in files_list]

    def exists(self, path):
        category, ref_id, file_path = self._parse_path(path)
        assets = self._get_all_assets(category=category, ref_id=ref_id)
        files_list = []
        for asset in assets:
            if file_path and not asset.metadata.get("file_name", "").startswith(file_path):
                continue
            file_info = {
                "name": asset.metadata.get("file_name", ""),
                "size": asset.metadata.get("file_size", 0),
                "created_at": asset.created_at,
                "file_name": asset.metadata.get("file_name", ""),
            }
            files_list.append(file_info)
        return bool(files_list)

    def info(self, path, **kwargs):
        """
        Get file information like size, creation time, and file name for a specific asset.
        """
        return self.ls(path=path, detail=True)

    def mkdir(self, path, **kwargs):
        """
        Create a directory-like structure (not supported for the Assets model).
        """
        category, ref_id, file_path = self._parse_path(path)
        if not file_path:
            raise ValueError("Operation not permitted at the root level")

        assets = self._get_all_assets(category=category, ref_id=ref_id)
        for asset in assets:
            if asset.metadata.get("file_name", "").startswith(file_path):
                return False

        empty_file = f"{path}.empty" if path.endswith("/") else f"{path}/.empty"
        self.touch(empty_file)

    def rmdir(self, path):
        """
        Remove a directory-like structure (not supported for the Assets model).
        """
        category, ref_id, file_path = self._parse_path(path)
        if not file_path:
            raise ValueError("Operation not permitted at the root level")

        if not file_path.endswith("/"):
            raise ValueError("Invalid directory path")

        assets = self._get_all_assets(category=category, ref_id=ref_id)
        for asset in assets:
            if asset.metadata.get("file_name", "").startswith(file_path):
                asset.delete()
        return True
