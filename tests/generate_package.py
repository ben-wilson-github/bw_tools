from pathlib import Path

from zipfile import ZipFile
import json
import os


def main():
    plugin_name = "bw_tools"
    version = "2.0.0"
    min_designer_version = "11.2.1"
    author = "Ben Wilson"
    email = "ben.q.wilson@gmail.com"
    platform = "any"
    metadata_format_version = "1"

    plugin_versioned_name = f"{plugin_name}_{version.replace('.', '_')}"

    plugin_dir = Path.cwd().parent

    ignore_folders = [
        "__pycache__",
        "bw_generate_slider_outputs",
        "bw_print_node_info",
    ]
    ignore_files = [".psd"]

    with ZipFile(f"{plugin_versioned_name}.sdplugin", "w") as zip_obj:
        for root, folders, files in os.walk(Path.cwd().joinpath(plugin_name)):
            abs_path = Path(root)
            rel_path = abs_path.relative_to(plugin_dir)
            if rel_path.name in ignore_folders:
                continue

            path = Path(plugin_versioned_name) / plugin_versioned_name
            for part in rel_path.parts[1:]:
                path = path.joinpath(part)
            rel_path = path

            for file_name in files:
                if os.path.splitext(file_name)[1] in ignore_files:
                    continue
                zip_obj.write(abs_path / file_name, rel_path / file_name)

        plugin_info = {
            "metadata_format_version": metadata_format_version,
            "name": plugin_versioned_name,
            "version": version,
            "author": author,
            "email": email,
            "min_designer_version": min_designer_version,
            "platform": platform,
        }
        plugin_info_path = Path.cwd() / "pluginInfo.json"
        with open(plugin_info_path, "w") as settings_file:
            json.dump(plugin_info, settings_file, indent=4)

        zip_obj.write(
            plugin_info_path, Path(f"/{plugin_versioned_name}/pluginInfo.json")
        )

        license_path = Path.cwd() / "LICENSE"
        zip_obj.write(
            license_path,
            Path(f"/{plugin_versioned_name}/{plugin_versioned_name}/LICENSE"),
        )

        main_init = Path.cwd() / "__init__.py"
        zip_obj.write(
            main_init,
            Path(
                f"/{plugin_versioned_name}/{plugin_versioned_name}/__init__.py"
            ),
        )

        readme = Path.cwd() / "README.md"
        zip_obj.write(
            readme,
            Path(
                f"/{plugin_versioned_name}/{plugin_versioned_name}/README.md"
            ),
        )


if __name__ == "__main__":
    main()
