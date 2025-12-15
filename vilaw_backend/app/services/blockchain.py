import hashlib
from datetime import datetime

class BlockchainService:
    @staticmethod
    def create_hash(content: str) -> tuple[str, str]:
        """Tạo mã Hash SHA-256 kèm timestamp, trả về (hash, timestamp)"""
        timestamp = datetime.now().isoformat()
        raw_data = f"{content}|{timestamp}"
        hash_val = hashlib.sha256(raw_data.encode()).hexdigest()
        return hash_val, timestamp

    @staticmethod
    async def log_transaction(tx_hash: str):
        """
        Giả lập gửi Hash lên Blockchain Network.
        Trong thực tế, code Web3.py sẽ nằm ở đây.
        """
        # print(f"🚀 [Blockchain] Gửi transaction: {tx_hash}")
        pass