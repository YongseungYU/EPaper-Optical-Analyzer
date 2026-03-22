from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = collect_submodules("streamlit")
hiddenimports += collect_submodules("streamlit.runtime")

datas, binaries, tmp_hiddenimports = collect_all("streamlit")
hiddenimports += tmp_hiddenimports
