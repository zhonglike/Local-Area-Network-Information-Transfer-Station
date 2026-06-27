!define PRODUCT_NAME "LANITS"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "LANITS Contributors"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "LANITS_Setup.exe"
InstallDir "$PROGRAMFILES\LANITS"
RequestExecutionLevel admin

Section "Install"
    SetOutPath "$INSTDIR"
    File "..\dist\LANITS.exe"
    File "..\icon.png"

    CreateDirectory "$APPDATA\LANITS\uploads"
    CreateDirectory "$APPDATA\LANITS\clipboard_files"

    CreateShortCut "$DESKTOP\LANITS.lnk" "$INSTDIR\LANITS.exe" "" "$INSTDIR\LANITS.exe" 0
    CreateDirectory "$SMPROGRAMS\LANITS"
    CreateShortCut "$SMPROGRAMS\LANITS\LANITS.lnk" "$INSTDIR\LANITS.exe"
    CreateShortCut "$SMPROGRAMS\LANITS\Uninstall.lnk" "$INSTDIR\uninst.exe"

    WriteUninstaller "$INSTDIR\uninst.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\LANITS.lnk"
    RMDir /r "$SMPROGRAMS\LANITS"
    RMDir /r "$INSTDIR"
    RMDir /r "$APPDATA\LANITS"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
