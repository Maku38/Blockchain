import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import WalletApp from './Wallet.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <WalletApp />
  </StrictMode>,
)
