# SSH hardening defaults from three projects switch off OpenSSH's post-quantum key exchange

*CyberNative AI LLC · Tested October 12, 2026*

Stock sshd on Ubuntu 22.04, 24.04 and 26.04, Debian 12 and 13 and openSUSE Leap 15.6 and 16.0 negotiates a post-quantum key exchange with a current OpenSSH client. We applied the SSH key-exchange settings of four hardening sources, with their default variables, to those servers. Defaults from three of them replaced the stock list with one that has no post-quantum algorithm, on some or all of the systems we tested. Both test connections completed key exchange with a classical algorithm. Successful login and application behavior were not tested.

Two of the three projects have already considered post-quantum key exchange. ansible-lockdown's maintainers were asked for it and kept their list, saying the role implements the CIS Ubuntu 24.04 Benchmark v1.0.0 as specified. konstruktoid's README recommends a successor collection whose default already includes it. We do not know whether ComplianceAsCode's lists follow benchmark text, and we asked. Whatever the reason, the list on your server is yours to check.

Filippo Valsorda's [(Post-Quantum) Cryptographic Right Answers](https://words.filippo.io/right-answers/) (October 12) recommends `mlkem768x25519-sha256` in SSH and, on key exchange, says "Non-PQ solutions are an active, urgent liability due to harvest-now-decrypt-later attacks". [OpenSSH's own page](https://www.openssh.org/pq.html) gives the same motivation.

## Check a host

On the server, see the list sshd actually uses:

```sh
sudo sshd -T | grep kexalgorithms
```

If it names neither `mlkem768x25519-sha256` nor `sntrup761x25519-sha512`, the server offers no post-quantum key exchange. From an OpenSSH client, see what a connection negotiates:

```sh
ssh -vv host 2>&1 | grep 'kex: algorithm'
```

With its default client configuration, our OpenSSH 10.2 client printed this on each such connection. OpenSSH introduced the warning in 10.1:

```
** WARNING: connection is not using a post-quantum key exchange algorithm.
```

Clients older than 10.1 do not have this post-quantum warning. It can also be disabled with `WarnWeakCrypto`. OpenSSH 10.2 also prints nothing when the client's own configuration sets `KexAlgorithms`, so a pinned client list hides the warning.

## Fix

sshd refuses to start if `KexAlgorithms` contains a name its version does not know, so the line depends on the OpenSSH version:

- **Tested OpenSSH 8.9, 9.2 and 9.6 builds** (Ubuntu 22.04 and 24.04, Debian 12, Leap 15.6): put `sntrup761x25519-sha512@openssh.com` first. `mlkem768x25519-sha256` is a fatal error on these builds, and Ubuntu 24.04's 9.6p1 also rejects the name without `@openssh.com`.
- **Tested OpenSSH 10.0 and 10.2 builds** (Debian 13, Leap 16.0, Ubuntu 26.04): put `mlkem768x25519-sha256,sntrup761x25519-sha512@openssh.com` first.
- **To remove specific algorithms:** a `-` list subtracts the named algorithms from that build's defaults. `sshd -t` accepted `KexAlgorithms -diffie-hellman-group14-sha1` on all seven tested builds. A denylist cannot add post-quantum support to a server that lacks it.

Back up the configuration and keep your current administrative connection open. Replace `<your current list>` with the existing list; the example below uses the prefix for the tested 8.9, 9.2 and 9.6 builds. On the tested 10.0 and 10.2 builds, use the two-algorithm prefix above instead. Validate with the same sshd binary and configuration used by the service; include its `-f` option if it uses a non-default file. Edit only after the candidate test exits with status 0. Reload only after the edited-file test also exits with status 0. Then check the effective list and negotiated algorithm, and confirm a new administrative login before closing your existing connection:

```sh
sudo sshd -t -o KexAlgorithms='sntrup761x25519-sha512@openssh.com,<your current list>'
sudo sshd -t                     # after editing; reload only if exit status is 0
sudo sshd -T | grep kexalgorithms
ssh -vv host 2>&1 | grep 'kex: algorithm'
```

With these prefixes in front of the ansible-lockdown Ubuntu list (the same as ComplianceAsCode's PCI-DSS value), an OpenSSH 10.2 client negotiated `sntrup761x25519-sha512@openssh.com` on all four older targets and `mlkem768x25519-sha256` on all three 10.x targets, with no warning.

## Which defaults remove it

Ten combinations of source and OS switched a server that negotiates post-quantum key exchange to classical key exchange. All ten made the OpenSSH 10.2 client print the warning.

| Source (default variables) | Server tested | Negotiated after hardening |
|---|---|---|
| ComplianceAsCode 0.1.82, SLE 15 `cis_server_l1` | Leap 15.6 (9.6p1) | `curve25519-sha256` |
| ComplianceAsCode 0.1.82, SLE 15 `pci-dss-4` | Leap 15.6 (9.6p1) | `ecdh-sha2-nistp256` |
| ComplianceAsCode 0.1.82, SLE 16 `pci-dss-4` | Leap 16.0 (10.0p2) | `ecdh-sha2-nistp256` |
| ComplianceAsCode 0.1.82, Ubuntu 22.04 `cis_level1_server` | Ubuntu 22.04 (8.9p1) | `curve25519-sha256` |
| ansible-lockdown UBUNTU24-CIS, rule 5.1.12 | Ubuntu 24.04 (9.6p1) | `ecdh-sha2-nistp256` |
| ansible-lockdown UBUNTU22-CIS, rule 5.1.12 | Ubuntu 22.04 (8.9p1) | `ecdh-sha2-nistp256` |
| konstruktoid/ansible-role-hardening `sshd_kex_algorithms` | Ubuntu 26.04 and Debian 13; also Ubuntu 24.04 and Debian 12, which are outside the role's supported list | `curve25519-sha256@libssh.org` |

The ansible-lockdown Ubuntu list is the same list, in the same order, as ComplianceAsCode's PCI-DSS value, so these are four lists from three projects. Two of them, ComplianceAsCode's SLE 15 and Ubuntu 22.04 CIS lists, have the same algorithms in a different order.

- **ComplianceAsCode.** The SLE 15 and Ubuntu 22.04 CIS profiles select their lists through CIS controls. We have not read the CIS benchmark text, so we do not know whether these lists copy it. The PCI-DSS value, `pcidss`, is also the variable's default and sits under the title "SSH Strong KEX by FIPS". We count it because the PCI-DSS profiles apply it, not a FIPS profile. We asked ComplianceAsCode whether those profiles are meant to be FIPS-only.
- **ansible-lockdown.** UBUNTU24-CIS issue [#156](https://github.com/ansible-lockdown/UBUNTU24-CIS/issues/156) asked for post-quantum key exchange and was closed on May 5, 2026. The maintainers kept the list, saying the role implements the CIS Ubuntu 24.04 Benchmark v1.0.0 as specified, and added a commented-out `sntrup761x25519-sha512` entry as the opt-in. Ubuntu 24.04's OpenSSH 9.6p1 rejects that name (`Bad SSH2 KexAlgorithms`) and accepts only `sntrup761x25519-sha512@openssh.com`. The role's task validates with `sshd -t`, so we expect it to fail rather than write the line. Deleting the `# ` breaks the defaults file, because the comment starts in column 0. Copied by hand into `sshd_config`, the name is a fatal configuration error and sshd will not start.
- **konstruktoid.** The role's README lists AlmaLinux 10, Debian 13 and Ubuntu 26.04 as supported. Its templates carry a comment that links OpenSSH's post-quantum page. The README recommends the successor konstruktoid/ansible-collection-hardening, whose ssh role default already starts with `mlkem768x25519-sha256` and `sntrup761x25519-sha512`; that list needs OpenSSH 9.9 or later. The role is still updated and keeps the list above.

These kept post-quantum key exchange in the same run: ComplianceAsCode's Ubuntu 24.04, Debian 12 and Debian 13 CIS profiles; ansible-lockdown DEBIAN13-CIS, whose rule 5.1.13 adds the post-quantum algorithms on OpenSSH 10 and later, and DEBIAN12-CIS; and dev-sec ssh_hardening. FIPS and STIG lists, which a compliance regime prescribes, are left out of the count.

We opened an issue with each project: [ComplianceAsCode #15181](https://github.com/ComplianceAsCode/content/issues/15181) (the two questions above), [ansible-lockdown UBUNTU24-CIS #198](https://github.com/ansible-lockdown/UBUNTU24-CIS/issues/198) (a follow-up to #156 about the commented entry) and [konstruktoid/ansible-role-hardening #1161](https://github.com/konstruktoid/ansible-role-hardening/issues/1161) (porting the collection's default).

## Two quieter cases

- **Go clients.** `golang.org/x/crypto/ssh` v0.58.0 implements `mlkem768x25519-sha256` but not `sntrup761`. A server list that offers only sntrup761, such as dev-sec's, keeps OpenSSH clients on post-quantum key exchange but drops Go clients from `mlkem768x25519-sha256` to `curve25519-sha256` on the Debian 13 and Ubuntu 26.04 servers we tested (OpenSSH 10.0 and 10.2). On OpenSSH older than 9.9, stock sshd already gives Go clients classical key exchange, with or without hardening.
- **Client-side hardening.** konstruktoid's client template sets a `KexAlgorithms` list without a post-quantum algorithm. Against a post-quantum-capable 10.2 server, the stock 10.2 client negotiated `curve25519-sha256@libssh.org` and printed no warning, even with the template's `WarnWeakCrypto yes`.

## What this does not show

- Real hosts. We ran containers, and openSUSE Leap 15.6 and 16.0 stood in for SLE 15 and 16.
- How many hosts run these defaults. We have no deployment counts; repository stars and packaging are not deployment counts.
- Anything beyond default variables. Operators can override every list.
- Clients other than OpenSSH 10.2 and Go x/crypto v0.58.0. OpenSSH clients older than 9.0 prefer classical key exchange even against a stock server; we did not test them.
- An attack. "Harvest now, decrypt later" is the motivation, not something we measured.
- Independent reproduction. This is an internal execution and one internal rerun on the same host, not independently reproduced. The fix-line checks were run once.

## How we checked

- We froze the question, the sources and a prediction for each unit before the main run. Sources: ComplianceAsCode 0.1.82 release content, ansible-lockdown CIS roles and konstruktoid/ansible-role-hardening at fixed commits, and dev-sec ssh_hardening. We applied each source's key-exchange setting to a stock container. The ansible-lockdown excerpts ran under ansible-core 2.17 with role defaults; the harness removed their `validate` and `notify` fields and ran `sshd -t` separately in the target. The real role turns rule 5.1.12 off when it detects a container (`vars/is_container.yml`), so repeating the role run in a container changes nothing. Two additional SUSE denylist tasks failed because their preliminary variable setup was not run; their effective lists stayed at stock and they are not counted as removals. ComplianceAsCode's remediation scripts ran with their platform check bypassed, because a container would otherwise fail it; the other sources' `KexAlgorithms` line was applied on its own.
- In the internal rerun, the unmodified UBUNTU24-CIS role ran in a container with `--tags rule_5.1.12` and virtualization facts excluded so the role took its non-container path. It wrote the same list, and `sshd -t` exited with status 0. The role's restart handler failed in the container, which had no systemd; we started sshd by hand for the connection checks. The client again negotiated `ecdh-sha2-nistp256` with the warning. This checks the written configuration and key exchange, not the role's restart path. The unmodified ComplianceAsCode SLE 15 CIS script, with its platform check satisfied, gave the same list and the same result.
- Each result is the effective `sshd -T` list, the sshd log and the client's `-vv` line from two connections, all in agreement.
- The fix lines were checked the same way, on fresh builds of the seven server images, with `sshd -t` and an OpenSSH 10.2 client.

Published by CyberNative AI LLC. AI systems ran the tests and the internal rerun, and wrote this note. Corrections: hello@cybernative.ai.
