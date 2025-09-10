#!/usr/bin/env python3
"""
ApeX Omni Total Balance Checker (Updated with Environment Variables)
This script calculates your total tradeable funds across Spot and Contract accounts.
"""

import os
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ApexBalanceChecker:
    def __init__(self, api_key: str, secret: str, passphrase: str, is_testnet: bool = False):
        """
        Initialize the ApeX balance checker
        
        Args:
            api_key: Your API key
            secret: Your API secret
            passphrase: Your API passphrase
            is_testnet: Whether to use testnet (default: False for mainnet)
        """
        self.api_key = api_key
        self.secret = secret
        self.passphrase = passphrase
        
        if is_testnet:
            self.base_url = "https://testnet.omni.apex.exchange/api"
        else:
            self.base_url = "https://omni.apex.exchange/api"
    
    def _generate_signature(self, timestamp: str, method: str, path: str, data: str = "") -> str:
        """Generate API signature"""
        message = timestamp + method + path + data
        
        # Base64 encode the secret
        key = base64.standard_b64encode(self.secret.encode('utf-8'))
        
        # Create HMAC SHA256 signature
        signature = hmac.new(
            key,
            message.encode('utf-8'),
            hashlib.sha256
        )
        
        return base64.standard_b64encode(signature.digest()).decode()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated API request"""
        timestamp = str(int(time.time() * 1000))
        path = f"/v3{endpoint}"
        
        # Prepare query string for GET requests
        query_string = ""
        if method == "GET" and params:
            query_params = []
            for key, value in sorted(params.items()):
                if value is not None:
                    query_params.append(f"{key}={value}")
            if query_params:
                query_string = "&" + "&".join(query_params)
                path += "?" + "&".join(query_params)
        
        signature = self._generate_signature(timestamp, method, path, query_string)
        
        headers = {
            'APEX-SIGNATURE': signature,
            'APEX-TIMESTAMP': timestamp,
            'APEX-API-KEY': self.api_key,
            'APEX-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{path}"
        
        try:
            timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, headers=headers, json=params or {}, timeout=timeout)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}
    
    def get_account_data(self) -> Dict:
        """Get complete account data including balances and positions"""
        return self._make_request("GET", "/account")
    
    def get_account_balance(self) -> Dict:
        """Get account balance summary with equity calculations"""
        return self._make_request("GET", "/account-balance")
    
    def calculate_total_balance(self) -> Dict:
        """Calculate total tradeable balance across all accounts"""
        print("Fetching account data...")
        
        # Get detailed account data
        account_data = self.get_account_data()
        balance_data = self.get_account_balance()
        
        if not account_data or not balance_data:
            print("Failed to fetch account data")
            return {}
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "spot_balances": {},
            "contract_balances": {},
            "total_equity": 0,
            "available_balance": 0,
            "positions_summary": []
        }
        
        # Parse spot wallets (Omni account)
        spot_wallets = account_data.get("spotWallets", [])
        total_spot_value = 0
        
        print("\n=== SPOT ACCOUNT (OMNI) BALANCES ===")
        for wallet in spot_wallets:
            token = wallet.get("tokenId", "Unknown")  # tokenId maps to actual token
            balance = float(wallet.get("balance", 0))
            pending_deposit = float(wallet.get("pendingDepositAmount", 0))
            pending_withdraw = float(wallet.get("pendingWithdrawAmount", 0))
            
            available = balance - pending_withdraw + pending_deposit
            
            result["spot_balances"][token] = {
                "balance": balance,
                "available": available,
                "pending_deposit": pending_deposit,
                "pending_withdraw": pending_withdraw
            }
            
            # For USDT/USDC, add directly to total (assuming 1:1 with USD)
            if token in ["1", "17", "140"]:  # Common USDT/USDC token IDs
                total_spot_value += available
            
            print(f"  {token}: {balance:.6f} (Available: {available:.6f})")
        
        # Parse contract wallets (Perpetual account)
        contract_wallets = account_data.get("contractWallets", [])
        total_contract_value = 0
        
        print("\n=== CONTRACT ACCOUNT (PERPETUAL) BALANCES ===")
        for wallet in contract_wallets:
            asset = wallet.get("asset", "Unknown")
            balance = float(wallet.get("balance", 0))
            pending_deposit = float(wallet.get("pendingDepositAmount", 0))
            pending_withdraw = float(wallet.get("pendingWithdrawAmount", 0))
            
            available = balance - pending_withdraw + pending_deposit
            
            result["contract_balances"][asset] = {
                "balance": balance,
                "available": available,
                "pending_deposit": pending_deposit,
                "pending_withdraw": pending_withdraw
            }
            
            total_contract_value += available
            print(f"  {asset}: {balance:.6f} (Available: {available:.6f})")
        
        # Parse positions
        positions = account_data.get("positions", [])
        print("\n=== OPEN POSITIONS ===")
        
        for position in positions:
            if float(position.get("size", 0)) != 0:  # Only show non-zero positions
                symbol = position.get("symbol", "Unknown")
                side = position.get("side", "Unknown")
                size = float(position.get("size", 0))
                entry_price = float(position.get("entryPrice", 0))
                
                position_info = {
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "entry_price": entry_price,
                    "value": size * entry_price
                }
                
                result["positions_summary"].append(position_info)
                print(f"  {symbol}: {side} {size} @ {entry_price}")
        
        # Get summary from balance endpoint
        if balance_data:
            result["total_equity"] = float(balance_data.get("totalEquityValue", 0))
            result["available_balance"] = float(balance_data.get("availableBalance", 0))
            result["initial_margin"] = float(balance_data.get("initialMargin", 0))
            result["maintenance_margin"] = float(balance_data.get("maintenanceMargin", 0))
        
        # Calculate totals
        result["calculated_totals"] = {
            "spot_total": total_spot_value,
            "contract_total": total_contract_value,
            "combined_liquid_assets": total_spot_value + total_contract_value
        }
        
        return result
    
    def print_summary(self, balance_data: Dict):
        """Print a formatted summary of balances"""
        if not balance_data:
            print("No balance data available")
            return
        
        print("\n" + "="*60)
        print("           APEX OMNI BALANCE SUMMARY")
        print("="*60)
        
        # Official equity values from API
        print(f"Total Account Equity:     ${balance_data.get('total_equity', 0):,.2f}")
        print(f"Available Balance:        ${balance_data.get('available_balance', 0):,.2f}")
        print(f"Initial Margin Used:      ${balance_data.get('initial_margin', 0):,.2f}")
        print(f"Maintenance Margin:       ${balance_data.get('maintenance_margin', 0):,.2f}")
        
        # Breakdown by account type
        calc_totals = balance_data.get("calculated_totals", {})
        print(f"\nBREAKDOWN:")
        print(f"Spot Account (Omni):      ${calc_totals.get('spot_total', 0):,.2f}")
        print(f"Contract Account (Perp):  ${calc_totals.get('contract_total', 0):,.2f}")
        print(f"Combined Liquid Assets:   ${calc_totals.get('combined_liquid_assets', 0):,.2f}")
        
        # Position count
        positions = balance_data.get("positions_summary", [])
        active_positions = [p for p in positions if p["size"] != 0]
        print(f"\nActive Positions:         {len(active_positions)}")
        
        print("="*60)


def main():
    """
    Main function to run the balance checker
    Credentials are loaded from environment variables
    """
    
    # Load credentials from environment variables
    API_KEY = os.getenv('APEX_API_KEY')
    SECRET = os.getenv('APEX_SECRET') 
    PASSPHRASE = os.getenv('APEX_PASSPHRASE')
    IS_TESTNET = os.getenv('IS_TESTNET', 'false').lower() == 'true'
    
    # Validate credentials are provided
    if not all([API_KEY, SECRET, PASSPHRASE]):
        print("❌ Missing API credentials in environment variables!")
        print("\nRequired environment variables:")
        print("- APEX_API_KEY")
        print("- APEX_SECRET") 
        print("- APEX_PASSPHRASE")
        print("- IS_TESTNET (optional, defaults to false)")
        print("\nPlease check your .env file and ensure all credentials are set.")
        return
    
    if API_KEY == "your-api-key-here":
        print("❌ Please update your .env file with actual API credentials!")
        print("\nTo get your credentials:")
        print("1. Go to https://omni.apex.exchange/keyManagement (or testnet version)")
        print("2. Click 'Generate API' to create new credentials")
        print("3. Update your .env file with the actual values")
        return
    
    try:
        # Initialize the balance checker
        checker = ApexBalanceChecker(API_KEY, SECRET, PASSPHRASE, IS_TESTNET)
        
        print(f"Using {'TESTNET' if IS_TESTNET else 'MAINNET'} environment")
        
        # Calculate balances
        balance_data = checker.calculate_total_balance()
        
        if balance_data:
            # Print summary
            checker.print_summary(balance_data)
            
            # Check if auto-save is enabled
            auto_save = os.getenv('AUTO_SAVE_REPORTS', 'false').lower() == 'true'
            
            if auto_save:
                save_to_file = 'y'
            else:
                save_to_file = input("\nSave detailed data to JSON file? (y/n): ").lower().strip()
                
            if save_to_file == 'y':
                import json
                
                # Create reports directory if it doesn't exist
                reports_dir = os.getenv('REPORTS_DIR', './reports')
                os.makedirs(reports_dir, exist_ok=True)
                
                filename = os.path.join(reports_dir, f"apex_balance_{int(time.time())}.json")
                with open(filename, 'w') as f:
                    json.dump(balance_data, f, indent=2)
                print(f"Data saved to {filename}")
        
        else:
            print("❌ Failed to retrieve balance data")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file contains correct API credentials")
        print("2. Ensure your API key has the required permissions")
        print("3. Check if you're using the right environment (testnet vs mainnet)")


if __name__ == "__main__":
    main()