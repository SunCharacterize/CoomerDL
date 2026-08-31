class DownloadSettingsService:
    NAMING_MODE_LABEL_TO_VALUE = {
        "Use File ID (default)": 0,
        "Use Sanitized Post Name": 1,
        "Post Name + Post ID Suffix": 2,
        "Post Date/Time + Post Name": 3,
    }

    NAMING_MODE_VALUE_TO_LABEL = {
        0: "Use File ID (default)",
        1: "Use Sanitized Post Name",
        2: "Post Name + Post ID Suffix",
        3: "Post Date/Time + Post Name",
    }

    def get_naming_options(self):
        return list(self.NAMING_MODE_LABEL_TO_VALUE.keys())

    def get_naming_label_from_setting(self, value):
        if isinstance(value, int):
            return self.NAMING_MODE_VALUE_TO_LABEL.get(value, self.NAMING_MODE_VALUE_TO_LABEL[0])

        if isinstance(value, str):
            if value in self.NAMING_MODE_LABEL_TO_VALUE:
                return value

            try:
                numeric = int(value)
                return self.NAMING_MODE_VALUE_TO_LABEL.get(numeric, self.NAMING_MODE_VALUE_TO_LABEL[0])
            except Exception:
                return self.NAMING_MODE_VALUE_TO_LABEL[0]

        return self.NAMING_MODE_VALUE_TO_LABEL[0]

    def parse_form_values(
        self,
        max_downloads_value,
        folder_structure_value,
        max_retries_value,
        retry_interval_value,
        file_naming_mode_label,
    ):
        max_downloads = int(max_downloads_value)
        max_retries = int(max_retries_value)
        retry_interval = float(retry_interval_value)
        numeric_mode = self.NAMING_MODE_LABEL_TO_VALUE.get(file_naming_mode_label, 0)

        return {
            "max_downloads": max_downloads,
            "folder_structure": folder_structure_value,
            "max_retries": max_retries,
            "retry_interval": retry_interval,
            "file_naming_mode": numeric_mode,
        }

    def apply_to_settings(self, settings: dict, parsed_values: dict):
        settings["max_downloads"] = parsed_values["max_downloads"]
        settings["folder_structure"] = parsed_values["folder_structure"]
        settings["max_retries"] = parsed_values["max_retries"]
        settings["retry_interval"] = parsed_values["retry_interval"]
        settings["file_naming_mode"] = parsed_values["file_naming_mode"]
        return settings

    def apply_to_downloader(self, downloader, parsed_values: dict):
        if not downloader:
            return

        if hasattr(downloader, "update_max_downloads"):
            downloader.update_max_downloads(parsed_values["max_downloads"])
        else:
            downloader.max_workers = parsed_values["max_downloads"]

        downloader.max_retries = parsed_values["max_retries"]
        downloader.retry_interval = parsed_values["retry_interval"]
        downloader.file_naming_mode = parsed_values["file_naming_mode"]