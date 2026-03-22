from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = collect_submodules("plotly")

datas, binaries, tmp_hiddenimports = collect_all("plotly")
hiddenimports += tmp_hiddenimports
