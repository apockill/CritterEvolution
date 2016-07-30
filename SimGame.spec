# -*- mode: python -*-

block_cipher = None


a = Analysis(['SimGame.py'],
             pathex=['F:\\Google Drive\\Projects\\Project - Critter Evolution - 2016 to Present'],
             binaries=None,
             datas=None,
             hiddenimports=['FixTk', 'scipy.linalg', 'scipy.linalg.cython_blas', 'scipy.linalg.cython_lapack'],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='SimGame',
          debug=False,
          strip=None,
          upx=True,
          console=True )
