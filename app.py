# app.py
import argparse
import sys
from web3 import Web3

BANNER = "🔐 CREATE2 Soundness Verifier"

def to_bytes(hex_or_0x: str) -> bytes:
    if hex_or_0x.startswith("0x") or hex_or_0x.startswith("0X"):
        hex_or_0x = hex_or_0x[2:]
    if len(hex_or_0x) % 2 == 1:
        hex_or_0x = "0" + hex_or_0x  # pad to even length
    return bytes.fromhex(hex_or_0x)

def left_pad_32(b: bytes) -> bytes:
    if len(b) > 32:
        raise ValueError("Salt must be <= 32 bytes")
    return b.rjust(32, b"\x00")

def compute_create2(deployer: str, salt_hex: str, init_code_hex: str) -> str:
    deployer = Web3.to_checksum_address(deployer)
    salt = left_pad_32(to_bytes(salt_hex))
    init_code = to_bytes(init_code_hex)
    init_code_hash = Web3.keccak(init_code)
    data = b"\xff" + bytes.fromhex(deployer[2:]) + salt + init_code_hash
    create2_hash = Web3.keccak(data)
    address = "0x" + create2_hash.hex()[-40:]
    return Web3.to_checksum_address(address)

def keccak_hex(data: bytes) -> str:
    return Web3.keccak(data).hex()

def main():
    parser = argparse.ArgumentParser(
        description="Verify CREATE2 determinism and (optionally) runtime bytecode hash on-chain."
    )
    parser.add_argument("--rpc-url", required=True, help="Ethereum-compatible RPC URL (e.g., Infura/Alchemy/Aztec-compatible endpoint)")
    parser.add_argument("--deployer", required=True, help="Deployer address (EOA or factory) that calls CREATE2")
    parser.add_argument("--salt", required=True, help="Salt (hex, with or without 0x; will be left-padded to 32 bytes)")
    parser.add_argument("--init-code", required=True, help="Contract init code (hex, with or without 0x)")
    parser.add_argument("--expected-code-hash", help="Optional expected Keccak-256 of deployed runtime bytecode (0x...)")
    args = parser.parse_args()

    print(BANNER)
    print("")

    # Compute deterministic address
    try:
        target = compute_create2(args.deployer, args.salt, args.init_code)
    except Exception as e:
        print(f"❌ Failed to compute CREATE2 address: {e}")
        sys.exit(1)

    init_code_hash = keccak_hex(to_bytes(args.init_code))
    print(f"RPC URL: {args.rpc_url}")
    print(f"Deployer: {Web3.to_checksum_address(args.deployer)}")
    print(f"Salt (hex, 32-byte left-padded): 0x{left_pad_32(to_bytes(args.salt)).hex()}")
    print(f"Init code hash: {init_code_hash}")
    print(f"Deterministic address (CREATE2): {target}")

    # Connect and fetch on-chain code
    w3 = Web3(Web3.HTTPProvider(args.rpc_url))
    if not w3.is_connected():
        print("❌ RPC connection failed")
        sys.exit(1)

    try:
        onchain_code = w3.eth.get_code(target)
    except Exception as e:
        print(f"❌ Failed to fetch on-chain code: {e}")
        sys.exit(1)

    if len(onchain_code) == 0:
        print("ℹ️ No runtime bytecode found at computed address (not deployed yet).")
        # If user provided an expected hash, we can't compare—treat as non-matching
        if args.expected_code_hash:
            print("❌ Soundness check: FAILED (no code to compare).")
            sys.exit(2)
        else:
            # No expectation set; determinism proven, deployment pending
            print("✅ Deterministic address computed. Deploy to this address to complete verification.")
            sys.exit(0)

    runtime_hash = Web3.keccak(onchain_code).hex()
    print(f"Runtime bytecode hash: {runtime_hash}")

    if args.expected_code_hash:
        # Normalize both to lowercase 0x...
        expected = args.expected_code_hash.lower()
        if not expected.startswith("0x"):
            expected = "0x" + expected
        if expected == runtime_hash.lower():
            print("✅ Soundness check: PASSED (runtime bytecode hash matches expected).")
            sys.exit(0)
        else:
            print("❌ Soundness check: FAILED (runtime bytecode hash does not match expected).")
            sys.exit(2)
    else:
        print("✅ Code present at deterministic address. To assert full soundness, provide --expected-code-hash.")
        sys.exit(0)

if __name__ == "__main__":
    main()
