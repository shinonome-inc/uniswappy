# liquidity_leak_test.py
# Author: Ian Moore ( imoore@syscoin.org )
# Date: Aug 2023

TEST_PATH = "python/test/defi/process/liquidity"

import os
import sys
import unittest   
sys.path.append(os.getcwd().replace(TEST_PATH,""))

from python.prod.cpt.factory import Factory
from python.prod.cpt.exchg import Exchange
from python.prod.cpt.erc import ERC20
from python.prod.cpt.erc import DOASYSERC20
from python.prod.cpt.erc import IndexERC20
from python.prod.cpt.vault import IndexVault
from python.prod.defi.process.liquidity import AddLiquidity
from python.prod.defi.process.mint import SwapIndexMint
from python.prod.defi.process.liquidity import AddLiquidity
from python.prod.defi.process.liquidity import RemoveLiquidity
from python.prod.cpt.index import RebaseIndexToken
from python.prod.cpt.quote import LPQuote
import numpy as np 

USER_NM = 'user0'
DAI_AMT = 10000
SYS_AMT = 100000

class Test_LiquidityLeak(unittest.TestCase):
   
    def setup_lp(self, factory, tkn1, tkn2, lp_nm):
        return factory.create_exchange(tkn1, tkn2, symbol=lp_nm, address="0x012")
    
    def add_liquidity1(self, tkn_x, itkn_y, lp_in, iVault, amt_in):
        parent_lp = lp_in.factory.parent_lp
        parent_tkn = itkn_y.parent_tkn
        itkn_nm = itkn_y.token_name
        SwapIndexMint(iVault).apply(parent_lp, parent_tkn, USER_NM, amt_in)
        mint_itkn_deposit = iVault.index_tokens[itkn_nm]['last_lp_deposit']
        tkn_amount1 = LPQuote(False).get_amount_from_lp(parent_lp, tkn_x, mint_itkn_deposit) 
        price_itkn = tkn_amount1/mint_itkn_deposit 
        AddLiquidity(price_itkn).apply(lp_in, itkn_y, USER_NM, mint_itkn_deposit)   
        
    def add_liquidity2(self, itkn, lp_in, iVault, amt_in):
        itkn_nm = itkn.token_name
        parent_tkn = itkn.parent_tkn
        parent_lp = lp_in.factory.parent_lp
        SwapIndexMint(iVault).apply(parent_lp, parent_tkn, USER_NM, amt_in)
        mint_itkn_deposit = iVault.index_tokens[itkn_nm]['last_lp_deposit']
        tkn_amount1 = LPQuote(False).get_amount_from_lp(parent_lp, parent_tkn, mint_itkn_deposit) 
        price_itkn = tkn_amount1/mint_itkn_deposit 

        itkn1_deposit = 0.5*mint_itkn_deposit
        itkn2_deposit = 0.5*mint_itkn_deposit
        lp_in.add_liquidity(USER_NM, itkn1_deposit, itkn2_deposit, itkn1_deposit, itkn2_deposit)           
    
    def setup(self, sys1, dai1):
        
        iVault1 = IndexVault('iVault1', "0x7")
        iVault2 = IndexVault('iVault2', "0x7")      
        
        factory = Factory("SYS pool factory", "0x2")
        lp = self.setup_lp(factory, sys1, dai1, 'LP')
        lp.add_liquidity(USER_NM, SYS_AMT, DAI_AMT, SYS_AMT, DAI_AMT)           
              
        sys2 = ERC20("SYS", "0x09")
        isys1 = IndexERC20("iSYS", "0x09", sys1, lp)         
        lp1 = self.setup_lp(factory, sys2, isys1, 'LP1')
        self.add_liquidity1(sys2, isys1, lp1, iVault1, 10000)
        
        dai2 = ERC20("DAI", "0x09")
        isys2 = IndexERC20("iSYS", "0x09", sys1, lp)          
        lp2 = self.setup_lp(factory, dai2, isys2, 'LP2')
        self.add_liquidity1(dai2, isys2, lp2, iVault1, 10000)
        
        dai3 = ERC20("DAI", "0x09")
        idai1 = IndexERC20("iDAI", "0x09", dai1, lp)         
        lp3 = self.setup_lp(factory, dai3, idai1, 'LP3')
        self.add_liquidity1(dai3, idai1, lp3, iVault1, 1000)
        
        sys3 = ERC20("SYS", "0x09")
        idai2 = IndexERC20("iDAI", "0x09", dai1, lp)           
        lp4 = self.setup_lp(factory, sys3, idai2, 'LP4')
        self.add_liquidity1(sys3, idai2, lp4, iVault1, 1000)  
        
        isys3 = IndexERC20("iSYS", "0x09", sys1, lp)
        idai3 = IndexERC20("iDAI", "0x09", dai1, lp)          
        lp5 = self.setup_lp(factory, isys3, idai3, 'LP5')
        self.add_liquidity2(isys3, lp5, iVault1, 10000)
        self.add_liquidity2(idai3, lp5, iVault2, 1000)        
        
        return lp, lp1, lp2, lp3, lp4, lp5

    
    def test_liquidity_leak0(self):
        
        sys1 = ERC20("SYS", "0x09") 
        dai1 = ERC20("DAI", "0x111")
        lp, lp1, lp2, lp3, lp4, lp5 = self.setup(sys1, dai1)
        
        pre_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        pre_lp_amt = lp.liquidity_providers[USER_NM]
        
        N_RUNS = 100
        for k in range(N_RUNS):
            lp1_amt = 100
            dai_amount1 = LPQuote(True).get_amount_from_lp(lp, dai1, lp1_amt) 
            price_idai = dai_amount1/lp1_amt 
            AddLiquidity(price_idai).apply(lp, dai1, USER_NM, lp1_amt) 
            RemoveLiquidity().apply(lp, dai1, USER_NM, abs(lp1_amt))          
           
        post_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        post_lp_amt = lp.liquidity_providers[USER_NM]
        
        self.assertEqual(round(pre_sys_amt,8), round(post_sys_amt,8))   
        self.assertEqual(round(pre_lp_amt,8), round(post_lp_amt,8)) 

    def test_liquidity_leak2(self):
        
        sys1 = ERC20("SYS", "0x09") 
        dai1 = ERC20("DAI", "0x111")
        
        lp, lp1, lp2, lp3, lp4, lp5 = self.setup(sys1, dai1)
        isys2 = IndexERC20("iSYS", "0x09", sys1, lp)
        
        pre_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        pre_lp_amt = lp.liquidity_providers[USER_NM]        
        pre_sys_amt2 = LPQuote(False).get_amount_from_lp(lp2, sys1, 1)
        pre_lp_amt2 = lp2.liquidity_providers[USER_NM]
        
        N_RUNS = 100
        for k in range(N_RUNS):
            vault_lp2_amt = 100
            sys_amount1 = LPQuote(True).get_amount_from_lp(lp, sys1, vault_lp2_amt) 
            price_idai = sys_amount1/vault_lp2_amt 
            AddLiquidity(price_idai).apply(lp2, isys2, USER_NM, vault_lp2_amt) 
            RemoveLiquidity().apply(lp2, isys2, USER_NM, abs(vault_lp2_amt))         
           
        post_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        post_lp_amt = lp.liquidity_providers[USER_NM]        
        post_sys_amt2 = LPQuote(False).get_amount_from_lp(lp2, sys1, 1)
        post_lp_amt2 = lp2.liquidity_providers[USER_NM]
        
        self.assertEqual(round(pre_sys_amt,8), round(post_sys_amt,8))   
        self.assertEqual(round(pre_lp_amt,8), round(post_lp_amt,8))         
        self.assertEqual(round(pre_sys_amt2,8), round(post_sys_amt2,8))   
        self.assertEqual(round(pre_lp_amt2,8), round(post_lp_amt2,8)) 
        
        
    def test_liquidity_leak4(self):
        
        sys1 = ERC20("SYS", "0x09") 
        dai1 = ERC20("DAI", "0x111")
        
        lp, lp1, lp2, lp3, lp4, lp5 = self.setup(sys1, dai1)
        idai2 = IndexERC20("iDAI", "0x09", dai1, lp) 
        
        pre_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        pre_lp_amt = lp.liquidity_providers[USER_NM]        
        pre_sys_amt4 = LPQuote(False).get_amount_from_lp(lp4, sys1, 1)
        pre_lp_amt4 = lp4.liquidity_providers[USER_NM]
        
        N_RUNS = 100
        for k in range(N_RUNS):
            vault_lp4_amt = 100
            dai_amount1 = LPQuote(True).get_amount_from_lp(lp, dai1, vault_lp4_amt) 
            price_idai = dai_amount1/vault_lp4_amt 
            AddLiquidity(price_idai).apply(lp4, idai2, USER_NM, vault_lp4_amt) 
            RemoveLiquidity().apply(lp4, idai2, USER_NM, abs(vault_lp4_amt))         
           
        post_sys_amt = LPQuote(False).get_amount_from_lp(lp, sys1, 1)
        post_lp_amt = lp.liquidity_providers[USER_NM]        
        post_sys_amt4 = LPQuote(False).get_amount_from_lp(lp4, sys1, 1)
        post_lp_amt4 = lp4.liquidity_providers[USER_NM]
        
        self.assertEqual(round(pre_sys_amt,8), round(post_sys_amt,8))   
        self.assertEqual(round(pre_lp_amt,8), round(post_lp_amt,8))         
        self.assertEqual(round(pre_sys_amt4,8), round(post_sys_amt4,8))   
        self.assertEqual(round(pre_lp_amt4,8), round(post_lp_amt4,8))         
      
        
if __name__ == '__main__':
    unittest.main()                  