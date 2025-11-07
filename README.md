# README.md
# CREATE2 Soundness Verifier

Overview
This small utility verifies the determinism and "soundness" of a contract deployment via CREATE2. It calculates the deterministic address from a deployer, salt, and init code; then, if the contract is deployed, it fetches the runtime bytecode and compares its Keccak-256 hash to an expected value (optional). This pattern is widely used across Ethereum and L2/zk ecosystems (including privacy or ZK-rollup projects such as Aztec) to guarantee reproducible, auditable deployments.

Files
- app.py — command-line script (Python).
- README.md — this guide.

Requirements
- Python 3.9+ (recommended 3.10+)
- An Ethereum-compatible RPC endpoint (e.g., mainnet, testnets, local devnet, or L2s with JSON-RPC support). You can also point at private networks used in research or privacy/ZK contexts (e.g., Aztec-style environments) if they expose a standard HTTP JSON-RPC interface.

Installation
1) Create and activate a virtual environment (optional).
2) Install dependency:
   pip install web3

Usage
Basic deterministic address derivation and on-chain inspection:
   python3 app.py --rpc-url https://mainnet.infura.io/v3/YOUR_KEY --deployer 0xDePl0Yer00000000000000000000000000000000 --salt 0x01 --init-code 0x600a600c600039600a6000f3fe602a60005260206000f3

Add a strong salt (any hex; will be left-padded to 32 bytes):
   --salt 0x000000000000000000000000000000000000000000000000000000000000c0de

Optional full soundness check by verifying runtime bytecode hash:
   python3 app.py --rpc-url https://mainnet.infura.io/v3/YOUR_KEY --deployer 0xDePl0Yer00000000000000000000000000000000 --salt 0xc0de --init-code 0x... --expected-code-hash 0xabcdef...

What the script does
1) Computes the CREATE2 address using:
   keccak256(0xff ++ deployer ++ salt32 ++ keccak256(init_code))[12:]
2) Connects to the RPC and reads the code at that address.
3) If code exists, prints its Keccak-256 hash.
4) If you provided --expected-code-hash, compares it and prints PASSED or FAILED.

Why this relates to "soundness"
- Determinism: CREATE2 ensures that the address is uniquely determined by deployer, salt, and init code. That enables reproducible builds and verifiable deployments often required by ZK systems and privacy networks (e.g., Aztec) and research into proof system soundness.
- Integrity: Verifying the runtime bytecode hash against an expected value provides a simple, transparent check that the on-chain artifact matches what was intended.

Expected output
- RPC connectivity status.
- Deployer, normalized 32-byte salt, init code hash.
- Deterministic CREATE2 address.
- If deployed: runtime bytecode hash, and optional soundness verdict.
- Exit code 0 on success or match; 2 on mismatch; 1 on errors.

Examples of results
- If no contract is deployed yet at the computed address:
   ℹ️ No runtime bytecode found at computed address (not deployed yet).
   ✅ Deterministic address computed. Deploy to this address to complete verification.
- If a contract is deployed and matches:
   ✅ Soundness check: PASSED (runtime bytecode hash matches expected).
- If deployed but does not match:
   ❌ Soundness check: FAILED (runtime bytecode hash does not match expected).

Notes
- The script accepts salt and init code as hex strings (with or without 0x). The salt will be left-padded to 32 bytes to match the CREATE2 specification.
- Runtime bytecode differs from init code. The script compares the on-chain runtime bytecode hash to your expected value (if provided).
- For air-gapped verifications, compute the expected runtime bytecode hash offline (e.g., from your compiler output) and pass it via --expected-code-hash.
- Networks like Aztec or research chains must expose a standard Ethereum JSON-RPC endpoint for this tool to connect. If the endpoint is incompatible, the script will fail to read code.
- Security tip: never leak private keys; this tool is read-only and does not sign transactions.

---

These sections will give the user all the necessary information to get started and troubleshoot any issues they may encounter. You can customize and expand these sections based on your needs.
