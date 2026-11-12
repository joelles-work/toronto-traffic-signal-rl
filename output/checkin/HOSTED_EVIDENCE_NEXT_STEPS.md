# Finish the hosted evidence links

The paper, local source, checkpoints, and offline W&B records are ready. The user has not created the remote projects yet. An email address alone does not authorize access to the account.

## GitHub

Connect the GitHub integration in this chat. Then create or select a repository (suggested name: `toronto-sumo-checkin`). A private repository is suitable if the instructor can access it. Publish the prepared source and evidence, verify the repository URL, and insert that actual URL into the report. Do not use the upstream TorontoSUMONetworks URL as though it were this project's repository.

## Weights & Biases

Sign in to the intended W&B account on this computer. Use the local W&B login flow if the Python SDK is not authenticated; do not paste passwords or API keys into chat or source files. The W&B entity is a username or team name, not an email address.

`experiments/pilot_v1/wandb_runs.json` identifies exactly six successful training records and one matched-dev comparison. Sync only those seven directories, not every directory under `wandb/`, because older baseline records and excluded failed attempts are also present. The installed CLI supports:

```text
.venv\Scripts\python.exe -m wandb sync --entity ENTITY --project toronto-tcs379 RUN_DIRECTORY
```

Replace `ENTITY` with the account/team name and `RUN_DIRECTORY` with one indexed directory. Repeat for the seven indexed records. This command uploads local evidence and can create the destination project. It has not been executed because account authentication is not available yet.

After synchronization, verify the actual run and project URLs in the intended account. Insert the verified repository and W&B URLs into Section III of the paper, regenerate the PDF, and repeat the two-page layout check. Offline directory names are not substitutes for the hosted URLs required by the checklist.

The check-in requires no further training or test-set evaluation at this stage.
