# Photo Upload Processing Sequence

This document describes the end-to-end runtime process order for the classroom photo flow, based on current architecture constraints in `README.md`, `f-spa/README.md`, and `ARCHITECTURE.md`.

## What This Diagram Covers

The sequence models the complete path from user action in the SPA to final processed face results:

1. Admission at ingress (`MS1`) with shared password validation against SSM.
2. Presigned upload flow to S3 for accepted requests.
3. Initial workflow state registration in `MS4`.
4. Asynchronous processing handoff to `MS2` via shared queue.
5. Face detection in `MS2` using Rekognition.
6. Post-detection source photo relocation in `MS2` from `uploaded/` to:
   - `processed/faces/` when faces were detected.
   - `processed/nofaces/` when no faces were detected.
7. Detection artifact persistence in `rekognition/` using relocated source key.
8. Asynchronous extraction handoff to `MS3` only when faces were detected.
9. Face extraction in `MS3` and result writes to S3.
10. State/result projection in `MS4` for frontend polling.
11. SPA polling and final result rendering.

It also includes the explicit invalid-password rejection branch, which terminates before entering protected upload/processing flow.

## Recommended Build Order

Implementation should follow dependency order implied by the sequence:

1. Validate shared platform readiness in `b-infra` (processing bucket, boundary queues/DLQs, and required outputs).
2. Implement `MS4` minimal contract-first slice:
   - Synchronous upload-init registration endpoint for `MS1`.
   - Status read endpoint for frontend polling.
   - Backing persistence model for workflow states.
3. Implement `MS1` admission flow:
   - Shared password validation via SSM Parameter Store.
   - Presigned upload URL issuance.
   - Mandatory synchronous `MS1 -> MS4` upload-init registration before success response.
4. Implement `MS2` detection worker:
   - Consume upload queue.
   - Run Rekognition detection.
   - Move processed source photo to `processed/faces` or `processed/nofaces`.
   - Persist detection artifacts.
   - Update `MS4` state and publish extraction job with relocated `sourceKey` when faces were found.
5. Implement `MS3` extraction worker:
   - Consume extraction queue.
   - Read original image + detection artifacts.
   - Create/store extracted face assets.
   - Finalize result state in `MS4`.
6. Wire frontend runtime to real `MS1` and `MS4` endpoints after backend contracts above are stable.

## Sequence Diagram Source

- Source file: `img/ita-photo-flow-sequence.mmd`

## Embedded Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Student/User
    participant SPA as f-spa (CloudFront SPA)
    participant MS1 as MS1 Ingress API/Lambda
    participant SSM as SSM Parameter Store
    participant S3 as S3 Processing Bucket
    participant MS4 as MS4 StateMgr API/Lambda + DynamoDB
    participant Q1 as SQS UploadedPhotosQueue
    participant MS2 as MS2 Detection Worker
    participant Rek as Amazon Rekognition
    participant Q2 as SQS FacesExtractionQueue
    participant MS3 as MS3 Faces Worker (Pillow)

    User->>SPA: Enter shared class password + select/capture photo
    SPA->>MS1: Request upload-init (password + photo metadata)
    MS1->>SSM: Read class shared password parameter
    SSM-->>MS1: Return stored password

    alt Password invalid
        MS1-->>SPA: 401/403 invalid password
        SPA-->>User: Show failure and stop flow
    else Password valid
        MS1->>S3: Create presigned PUT URL (uploads/...)
        MS1->>MS4: Register upload-init state (synchronous)
        MS4-->>MS1: State registration acknowledged
        MS1-->>SPA: Return uploadId + presigned URL + next state hints

        SPA->>S3: PUT photo via presigned URL
        S3-->>Q1: Emit upload event to UploadedPhotosQueue

        Q1-->>MS2: Deliver message (uploaded image reference)
        MS2->>Rek: DetectFaces(image)
        Rek-->>MS2: Face boxes + detection metadata
        alt Faces detected (>0)
            MS2->>S3: Move source photo to processed/faces/...
            MS2->>S3: Store detection artifact (rekognition/...) with processed/faces sourceKey
            MS2->>MS4: Update processing state (detected/processing)
            MS2-->>Q2: Publish extraction job (processed/faces source + boxes refs)
        else No faces detected (=0)
            MS2->>S3: Move source photo to processed/nofaces/...
            MS2->>S3: Store detection artifact (rekognition/...) with processed/nofaces sourceKey
            MS2->>MS4: Update failure state (NO_FACES_DETECTED)
        end

        Q2-->>MS3: Deliver extraction message
        MS3->>S3: Read processed/faces image + detection artifact
        MS3->>S3: Write extracted faces (faces/...)
        MS3->>MS4: Update completion state + result refs

        SPA->>MS4: Poll status by uploadId
        MS4-->>SPA: Return queued/processing/completed/failed + refs
        SPA-->>User: Show progress, then extracted faces and ranking-ready result
    end
```
