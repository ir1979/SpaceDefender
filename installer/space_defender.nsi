!define PRODUCT_NAME "Space Defender"
!define VERSION "2.1"
!define COMPANY_NAME "Ali Mortazavi"

!ifndef ARCH
!define ARCH "64"
!endif

OutFile ".\dist\win${ARCH}\${PRODUCT_NAME}-setup-${ARCH}.exe"
!if "${ARCH}" == "32"
  InstallDir "$PROGRAMFILES32\${PRODUCT_NAME}"
!else
  InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
!endif

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r ".\dist\win${ARCH}\SpaceDefender\*"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\SpaceDefender.exe"
SectionEnd
