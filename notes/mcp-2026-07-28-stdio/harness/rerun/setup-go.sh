set -e
export PATH=/envs/go/bin:$PATH
go version
for d in /src/adapters/go/*/; do n=$(basename $d); cp -r $d /scratch/b-$n; cd /scratch/b-$n
 GOFLAGS=-mod=readonly go build -trimpath -o /envs/gobin/$n-client ./client
 GOFLAGS=-mod=readonly go build -trimpath -o /envs/gobin/$n-server ./server
 echo built $n; done
