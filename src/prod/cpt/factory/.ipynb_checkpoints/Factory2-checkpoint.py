from python.prod.cpt.erc import ERC20
from python.prod.cpt.erc import DOASYSERC20
from python.prod.cpt.exchg import Exchange2 

class Factory2:

    """ 
        Create liquidity pools for given token pairs.
        
        Parameters
        ----------
        self.name : str
            Token name 
        self.address : str
            Token 0 name  
        self.token_to_exchange : dictionary
            Map of tokens to exchanges
        self.exchange_to_tokens : dictionary
            Map of exchanges to pair tokens          
           
        References
        ----------   
        - https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol
        - https://github.com/Uniswap/v2-periphery/blob/master/contracts/UniswapV2Router02.sol
    """     
    
    def __init__(self, name: str, address: str) -> None:
        self.name = name
        self.address = address
        self.token_to_exchange = {}
        self.exchange_to_tokens = {}

    def create_exchange(self, token0: ERC20, token1: ERC20, symbol: str, address : str):
        
        """ create_exchange

            Create liquidity pool (LP) exchange
                
            Parameters
            -------
            token0 : ERC20
                ERC20 token within LP pair     
            token1 : ERC20
                ERC20 token within LP pair       
            symbol : str
                name of exchange  
            address : float
                address of exchange  
                
            Returns
            -------
            new_exchange : Exchange
                newly created exchange that is also a LP token                    
        """         
        
        if self.exchange_to_tokens.get(f"{token0.token_name}/{token1.token_name}"):
            raise Exception("Exchange already created")
               
        new_exchange = Exchange2(
            self,
            token0.token_name,
            token1.token_name,
            f"{token0.token_name}/{token1.token_name}",
            symbol,
            address
        )       
        
        self.token_to_exchange[token0.token_name] = new_exchange
        self.exchange_to_tokens[new_exchange.name] = {token0.token_name: token0, 
                                                      token1.token_name: token1}
        return new_exchange

    def get_exchange(self, token):
        
        """ get_exchange

            Get exchange from given pair token
                
            Parameters
            -------
            token : ERC20
                receiving user address      
                
            Returns
            -------
            exchange : Exchange
                exchange from mapped token                    
        """         
        
        return self.token_to_exchange.get(token)

    def get_token(self, exchange):
        
        """ get_token

            Get token from exchange
                
            Parameters
            -------
            exchange : Exchange
                receiving user address      
                
            Returns
            -------
            token : ERC20 
                token from mapped exchange                     
        """          
        
        return self.exchange_to_token.get(exchange)

    def token_count(self):
        
        """ token_count

            Get token count from factory   
                
            Returns
            -------
            num token : int 
                number of tokens in factory                    
        """          
        
        return len(self.token_to_exchange)