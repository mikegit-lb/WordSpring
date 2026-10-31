# WordSpring Microsoft Store submission notes

## Package

WordSpring is a 64-bit packaged desktop app. `build_store_msix.ps1` makes an onedir PyInstaller payload, places it in an MSIX package with the Store assets, and unpacks the result to validate package structure. It deliberately leaves `edge-tts` out of the Store build, so speech stays offline through Windows SAPI. Study data and synthesized audio are kept under the user's local app-data folder.

Before the final package can be produced, reserve the app in Partner Center and copy the exact **Package/Identity Name**, **Publisher**, and **Publisher display name** from the app identity page. These values are case-sensitive and must not be guessed. Build with:

```powershell
.\build_store_msix.ps1 `
  -IdentityName "IDENTITY_FROM_PARTNER_CENTER" `
  -Publisher "PUBLISHER_FROM_PARTNER_CENTER" `
  -PublisherDisplayName "PUBLISHER_DISPLAY_NAME"
```

The output is `dist\WordSpring-1.0.1.0.msix`. Add `-RunAppCertKit` to run the Windows App Certification Kit in an active desktop session. Review its report and fix every blocking finding before submission.

The MSIX is not signed by this build script. Store submissions are re-signed by Microsoft after certification. Do not self-sign with a different publisher; that breaks the package identity.

The community PySide6 packages used here are offered under LGPLv3/GPLv3 terms. The Store builder removes the unused GPL-only Qt Virtual Keyboard payload and adds the LGPLv3 text and dependency notices to the app package. The publisher is responsible for satisfying the Qt LGPL requirements for the distributed app, or for using a suitable Qt commercial license. See `THIRD_PARTY_NOTICES.md` before publication.

## Store listing draft

See `store/listing-tr-TR.md` for the Turkish title, short and full descriptions, keywords, and support text. The three 1366×768 screenshots in `store/Screenshots` are rendered from the real Qt screens with a clean seed database. Store logos are under `store/Assets`.

## Required Partner Center work

1. Reserve **WordSpring** (or another available name) in Partner Center and use its exact identity values for the package.
2. Complete the Turkish (Türkiye) store listing, category, pricing, market selection, age-rating questionnaire, support contact, and required screenshots.
3. Publish the privacy text from `store/privacy-policy-tr.md` at a public HTTPS URL if Partner Center requests a privacy URL; enter that URL in the listing.
4. Upload the generated MSIX and submit it for certification.
5. Test installation, upgrade, uninstall, audio, and saved-progress behavior on a clean Windows 10 and Windows 11 device, including a machine without an English SAPI voice.

An active Partner Center developer account and the app's reserved identity are external account details; they are not present in this source workspace.
