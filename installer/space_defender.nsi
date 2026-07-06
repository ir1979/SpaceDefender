; ============================================================================
;  Space Defender - NSIS Installer Script
; ----------------------------------------------------------------------------
;  Invoked from build.bat as:
;      makensis /DARCH=32 space_defender.nsi
;      makensis /DARCH=64 space_defender.nsi
; ============================================================================

!define PRODUCT_NAME      "Space Defender"
!define PRODUCT_VERSION   "2.1.0.0"
!define PRODUCT_VERSION_3 "2.1.0"
!define COMPANY_NAME      "Ali Mortazavi"
!define PRODUCT_WEB       "https://github.com/anomalyco/SpaceDefender"
!define EXE_NAME          "SpaceDefender.exe"
!define UNINST_KEY        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

!ifndef ARCH
  !define ARCH "64"
!endif

!define ICON_FILE "..\assets\icons\spacedefender_large.ico"

; ---- Output / install directory --------------------------------------------
Name        "${PRODUCT_NAME} ${PRODUCT_VERSION_3} (${ARCH}-bit)"
OutFile     ".\dist\win${ARCH}\${PRODUCT_NAME}-setup-${ARCH}.exe"
BrandingText "${PRODUCT_NAME} ${PRODUCT_VERSION_3} - ${COMPANY_NAME}"

!if "${ARCH}" == "32"
  InstallDir "$PROGRAMFILES32\${PRODUCT_NAME}"
!else
  InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
!endif

InstallDirRegKey HKLM "Software\${PRODUCT_NAME}" "InstallDir"

RequestExecutionLevel admin
SetCompressor /SOLID lzma

; ---- Icons & branding ------------------------------------------------------
Icon          "${ICON_FILE}"
UninstallIcon "${ICON_FILE}"

; ---- Version metadata embedded in the setup .exe ---------------------------
VIProductVersion "${PRODUCT_VERSION}"
VIAddVersionKey "ProductName"     "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion"  "${PRODUCT_VERSION_3}"
VIAddVersionKey "CompanyName"     "${COMPANY_NAME}"
VIAddVersionKey "FileVersion"     "${PRODUCT_VERSION}"
VIAddVersionKey "FileDescription" "${PRODUCT_NAME} Installer (${ARCH}-bit)"
VIAddVersionKey "LegalCopyright"  "Copyright (C) ${COMPANY_NAME}"
VIAddVersionKey "OriginalFilename" "${PRODUCT_NAME}-setup-${ARCH}.exe"

; ---- Modern UI -------------------------------------------------------------
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON         "${ICON_FILE}"
!define MUI_UNICON       "${ICON_FILE}"

!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
;  Install
; ============================================================================
Section "Install"
  SetOutPath "$INSTDIR"
  SetOverwrite on

  ; Copy the entire PyInstaller bundle (SpaceDefender.exe + _internal\*)
  File /r ".\dist\win${ARCH}\SpaceDefender\*"

  ; Shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut  "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" \
                  "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0
  CreateShortCut  "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk" \
                  "$INSTDIR\Uninstall.exe"
  CreateShortCut  "$DESKTOP\${PRODUCT_NAME}.lnk" \
                  "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Remember install dir
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "Version"    "${PRODUCT_VERSION_3}"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "Arch"       "${ARCH}"

  ; Add/Remove Programs entry
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayName"     "${PRODUCT_NAME} (${ARCH}-bit)"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayVersion"  "${PRODUCT_VERSION_3}"
  WriteRegStr   HKLM "${UNINST_KEY}" "Publisher"       "${COMPANY_NAME}"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayIcon"     "$INSTDIR\${EXE_NAME}"
  WriteRegStr   HKLM "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKLM "${UNINST_KEY}" "URLInfoAbout"    "${PRODUCT_WEB}"
  WriteRegStr   HKLM "${UNINST_KEY}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegStr   HKLM "${UNINST_KEY}" "QuietUninstallString" "$\"$INSTDIR\Uninstall.exe$\" /S"
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
SectionEnd

; ============================================================================
;  Uninstall
; ============================================================================
Section "Uninstall"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk"
  RMDir  "$SMPROGRAMS\${PRODUCT_NAME}"

  ; Remove installed files
  RMDir /r "$INSTDIR\_internal"
  Delete   "$INSTDIR\${EXE_NAME}"
  Delete   "$INSTDIR\Uninstall.exe"
  RMDir    "$INSTDIR"

  DeleteRegKey HKLM "${UNINST_KEY}"
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"
SectionEnd
