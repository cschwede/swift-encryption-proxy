# swift-encryption-proxy

POC for a simple encryption proxy. Encrypt PUT request body, decrypt GET request body.

## Example

The sample assumes a local Swift proxy on 127.0.0.1:8080 (for example on devstack).
Start the encryption proxy:

    python reverse-proxy

The reverse proxy listens in port 8081. To up- and download use the following commands:

    > dd if=/dev/urandom of=testfile bs=1k count=1k
    > md5sum testfile 
    f0ee81accd351384299c761c91055d4c  testfile
    > swift --os-storage-url http://127.0.0.1:8081/v1/AUTH_e683ff01209049ecb107b71bf823fd4d upload test testfile 
    > swift --os-storage-url http://127.0.0.1:8081/v1/AUTH_e683ff01209049ecb107b71bf823fd4d download test testfile 
    testfile: md5sum != etag, f0ee81accd351384299c761c91055d4c != d1ac605d4cf6b91066d45386da55f755
    testfile [headers 0.303s, total 0.317s, 3.306 MB/s]
    > md5sum testfile 
    f0ee81accd351384299c761c91055d4c  testfile

As you can see the downloaded file is identical to the original uploaded file.
You'll get a warning from swiftclient because the remote etag is not identical to the MD5 of the downloaded file - which is 
expected as the remote version is encrypted. The encrypted file on Swift is of coure different:

    > swift download test testfile 
    > md5sum testfile 
    d1ac605d4cf6b91066d45386da55f755  testfile
