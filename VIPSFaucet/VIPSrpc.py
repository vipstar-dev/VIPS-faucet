import requests
import simplejson as json
import base58
import logging
import inspect
from decimal import Decimal, ROUND_DOWN

class VIPS:
	DEFAULT_FEE = Decimal("0.0001")
	ONE_SATOSHI = Decimal("0.00000001")

def round_satoshi(a):
	if isinstance(a, float):
		a = Decimal(a)
	return a.quantize(VIPS.ONE_SATOSHI, rounding=ROUND_DOWN)

class VIPSRPCErrorCode:
    #//! Standard JSON-RPC 2.0 errors
    RPC_INVALID_REQUEST  = -32600
    RPC_METHOD_NOT_FOUND = -32601
    RPC_INVALID_PARAMS   = -32602
    RPC_INTERNAL_ERROR   = -32603
    RPC_PARSE_ERROR      = -32700
    
    #//! General application defined errors
    RPC_MISC_ERROR                  = -1  #//! std::exception thrown in command handling
    RPC_FORBIDDEN_BY_SAFE_MODE      = -2  #//! Server is in safe mode and command is not allowed in safe mode
    RPC_TYPE_ERROR                  = -3  #//! Unexpected type was passed as parameter
    RPC_INVALID_ADDRESS_OR_KEY      = -5  #//! Invalid address or key
    RPC_OUT_OF_MEMORY               = -7  #//! Ran out of memory during operation
    RPC_INVALID_PARAMETER           = -8  #//! Invalid missing or duplicate parameter
    RPC_DATABASE_ERROR              = -20 #//! Database error
    RPC_DESERIALIZATION_ERROR       = -22 #//! Error parsing or validating structure in raw format
    RPC_VERIFY_ERROR                = -25 #//! General error during transaction or block submission
    RPC_VERIFY_REJECTED             = -26 #//! Transaction or block was rejected by network rules
    RPC_VERIFY_ALREADY_IN_CHAIN     = -27 #//! Transaction already in chain
    RPC_IN_WARMUP                   = -28 #//! Client still warming up
    
    #//! Aliases for backward compatibility
    RPC_TRANSACTION_ERROR           = RPC_VERIFY_ERROR
    RPC_TRANSACTION_REJECTED        = RPC_VERIFY_REJECTED
    RPC_TRANSACTION_ALREADY_IN_CHAIN= RPC_VERIFY_ALREADY_IN_CHAIN
    
    #//! P2P client errors
    RPC_CLIENT_NOT_CONNECTED        = -9  #//! Bitcoin is not connected
    RPC_CLIENT_IN_INITIAL_DOWNLOAD  = -10 #//! Still downloading initial blocks
    RPC_CLIENT_NODE_ALREADY_ADDED   = -23 #//! Node is already added
    RPC_CLIENT_NODE_NOT_ADDED       = -24 #//! Node has not been added before
    RPC_CLIENT_NODE_NOT_CONNECTED   = -29 #//! Node to disconnect not found in connected nodes
    RPC_CLIENT_INVALID_IP_OR_SUBNET = -30 #//! Invalid IP/Subnet
    
    #//! Wallet errors
    RPC_WALLET_ERROR                = -4  #//! Unspecified problem with wallet (key not found etc.)
    RPC_WALLET_INSUFFICIENT_FUNDS   = -6  #//! Not enough funds in wallet or account
    RPC_WALLET_ACCOUNTS_UNSUPPORTED = -11 #//! Accounts are unsupported
    RPC_WALLET_KEYPOOL_RAN_OUT      = -12 #//! Keypool ran out call keypoolrefill first
    RPC_WALLET_UNLOCK_NEEDED        = -13 #//! Enter the wallet passphrase with walletpassphrase first
    RPC_WALLET_PASSPHRASE_INCORRECT = -14 #//! The wallet passphrase entered was incorrect
    RPC_WALLET_WRONG_ENC_STATE      = -15 #//! Command given in wrong wallet encryption state (encrypting an encrypted wallet etc.)
    RPC_WALLET_ENCRYPTION_FAILED    = -16 #//! Failed to encrypt the wallet
    RPC_WALLET_ALREADY_UNLOCKED     = -17 #//! Wallet is already unlocked

VIPSRPCErrorString = {}
for m in inspect.getmembers(VIPSRPCErrorCode):
	if m[0][0:4] == "RPC_":
		if not VIPSRPCErrorString.has_key(m[1]):
			VIPSRPCErrorString[m[1]] = m[0]

def error2str(code):
	if VIPSRPCErrorString.has_key(code):
		return VIPSRPCErrorString[code]
	return "RPC_UNKNOWN_ERROR_CODE_%d" % code

class VIPSRPCException(Exception):
	def __init__(self, m, c, id, method, param):
		super(Exception, self).__init__(m, c, error2str(c), id, method, param)

	def message(self):
		return self.args[0]
	
	def code(self):
		return self.args[1]

	def codestr(self):
		return self.args[2]

	def id(self):
		return self.args[3]

	def method(self):
		return self.args[4]

	def param(self):
		return self.args[5]

class VIPSRPCInvalidValue(Exception):
	def __init__(self, m, v):
		super(Exception, self).__init__(m, v)

class VIPSRPC:
	def __init__(self, username, password, host = "127.0.0.1", port = 31916, testnet = False):
		self.host = host
		self.port = port
		self.auth = (username, password)
		self.id = 0
		self.headers = {'content-type': 'application/json'}
		if not testnet:
			self.setmainnet(port)
		else:
			if port != 31916 and port != 32916:
				self.settestnet(port)
			else:
				self.settestnet()

	def setmainnet(self, port = 31916):
		self.addr_prefix = "\x46"
		self.port = port

	def settestnet(self, port = 32916):
		self.addr_prefix = "\x84"
		self.port = port

	def checkaddr(self, addr):
		try:
			d = base58.b58decode_check(addr)
			if d[0] == self.addr_prefix:
				return True
			return False
		except:
			return False
		
	def dorpc(self, method, params):
		url = "http://%s:%d" % (self.host, self.port)
		payload = {
			"jsonrpc": "1.0",
			"method": method,
			"params": params,
			"id": self.id
		}
		self.id += 1
		#print json.dumps(payload)
		r = requests.post(url, data=json.dumps(payload), headers=self.headers, auth=self.auth)
		response = json.loads(r.content, parse_float=Decimal)
		if response["error"] != None:
			raise VIPSRPCException(
				response["error"]["message"],
				response["error"]["code"],
				response["id"],
				method, params)
		return response["result"]

	def getinfo(self):
		return self.dorpc("getinfo", [])
	
	def getbalance(self, account = "", minconf = 1, includeWatchonly = False):
		return self.dorpc("getbalance", [account, minconf, includeWatchonly])

	# fromaddr = "" or "addr"
	# toaddrset = {"addr": amount, "addr": amount, ...}
	# subtraddrs = ["addr", "kaddr", ...]
	def sendmany(self, fromaddr, toaddrset, minconf = 1, comment = "", subtraddrs = []):
		if not fromaddr == "" and not self.checkaddr(fromaddr):
			raise VIPSRPCInvalidValue("sendmany: invalid from_address format", fromaddr)

		for addr in toaddrset.keys():
			if not self.checkaddr(addr):
				raise VIPSRPCInvalidValue("sendmany: invalid to_address format", addr)

		for addr in subtraddrs:
			if not self.checkaddr(addr):
				raise VIPSRPCInvalidValue("sendmany: invalid subtractfeefromamount address format", addr)

		return self.dorpc("sendmany", [fromaddr, toaddrset, minconf, comment, subtraddrs])

	def gettransaction(self, tid, watchonly = False):
		return self.dorpc("gettransaction", [tid, watchonly])
	
if __name__ == '__main__':
	rpc = VIPSRPC("VIPSrpcuser", "VIPSrpcpass", testnet = False)
	#rpc.settestnet()
	
	print(rpc.checkaddr("VBEdiRVXbEvoJG5w324sv6QrZrgAHBE6Q9"))
	print(rpc.checkaddr("VEU3r2Lx3gG72h7BFpkTpiTi6JtNqSHBGy"))

	#tid = rpc.sendmany("", {"VBEdiRVXbEvoJG5w324sv6QrZrgAHBE6Q9": Decimal(1)})
	#print tid
	#print rpc.gettransaction(tid)

	print(rpc.checkaddr("VKGaMkNj1CzGiHUtvSLwPB3KY9uYv8JHra"))



