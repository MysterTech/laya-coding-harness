# macOS service-launch QA

Status: isolated preflight passed; production implementation and native app-exit acceptance pending.

Workbenchtwofiles: initial18stubRED, first40GREEN; reviewloadedidentity/diagnostics corrected via8REDthen48GREEN. Native ten-secondlaunchthrottle discovery led to one-definitionassertionREDthen48GREEN; controller48passed2.40s, independent48passed2.37s/APPROVED. Final generatedpreflightplan c22dda8; WIP task-1 throughr3 preserved. No UI/copychanges, visualN/A.

Native round1 startup/advice/logappend passed; controllerhealthpollingresetidleclock, so idle measurement was invalid (notproductdefect). Round2 quietidleexit0, refusedrestart andSIGTERMstop/noautorestartpassed; rapidrestarthitdefaultlaunchdthrottle. Both exacttemporaryjobs cleaned/absent. Reducedprivate evidence native-round-1.json/native-round-2.json.

Final native round3 with ThrottleInterval0: SS277.436ms/empty/exit0; UPS75.296ms/exactfakeadvice/exit0/onedecidedrow. Service log sentinel preserved (append), home0700/plist0600/log0600. Jobresourceandjetsamcoalitions are named for its own uniquelyscopedlabel. Quietidleexit0/runs1/noautorestart; refusedprompt79.036ms/started_service andnewPID; explicitSIGTERM/runs2/noautorestart; SIGKILL/runs3/noautorestart; model-loadfailure yieldedthree not_ready rows on samePID; fourconcurrentlaunches all exit0 with onePID/runs5. Cleanuptrue and exactjobprint113/absent. Fakeonly, temporaryprivatehome/freeport, no standard47913/realhome/models/loginsettings. Private native-observed.json preserves reducedobservations. App-exit survival is not inferred from these observations.
