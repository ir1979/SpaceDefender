!define PRODUCT_NAME "Space Defender"
!define VERSION "2.1"
!define COMPANY_NAME "Ali Mortazavi"

!ifndef ARCH
!define ARCH "64"
!endif

OutFile "..\dist\win${ARCH}\${PRODUCT_NAME}-setup-${ARCH}.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "..\dist\win${ARCH}\*"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\SpaceDefender.exe"
SectionEnd
