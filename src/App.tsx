import React from 'react'
import { useState } from 'react'

import './App.css'
import SpreadSheet from './components/spread_sheet'

const App = () => {
  const [count, setCount] = useState(0)
  const [rows, setRows] = useState([])

  return (
    <div>
      <SpreadSheet /> 
      <div className="card">
        <label>行数: {rows.length}</label>
      </div>  
    </div>
  )
}

export default App
