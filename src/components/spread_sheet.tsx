import React, { useState } from 'react';
import axios from 'axios';
import './spread_sheet.css';
import { v4 as uuidv4 } from 'uuid';
import { jsPDF } from 'jspdf';

// Define a type for the spreadsheet row
interface SpreadsheetRow {
  id: string;
  account: string;
  businessAccount: string;
  postContentA: string;
  postContentB: string;
  postContentC: string;
  label: string;
}

// Update the API endpoint to point to the Flask server
const API_ENDPOINT = 'http://localhost:8080/post'; // Assuming the Flask server runs locally on port 8080
const API_TOKEN = 'your_api_token_here';

// Function to post content to an account
const postToAccount = async (account: string, businessAccount: string, content: string) => {
  try {
    const response = await axios.post(API_ENDPOINT, {
      account,
      businessAccount,
      content,
    }, {
      headers: {
        Authorization: `Bearer ${API_TOKEN}`,
      },
    });
    console.log(`Posted to ${account} (Business: ${businessAccount}): ${response.data}`);
  } catch (error: any) {
    console.error(`Error posting to ${account} (Business: ${businessAccount}):`, error.response ? error.response.data : error.message);
  }
};

// Function to send an auto-reply
const autoReply = async (content: string) => {
  try {
    const response = await axios.post(`${API_ENDPOINT}/reply`, {
      content,
    }, {
      headers: {
        Authorization: `Bearer ${API_TOKEN}`,
      },
    });
    console.log(`Auto-replied: ${response.data}`);
  } catch (error: any) {
    console.error('Error sending auto-reply:', error.response ? error.response.data : error.message);
  }
};

// スプレッドシートのデータを管理し、投稿や自動返信を行うコンポーネント
const SpreadSheet = () => {
  const [rows, setRows] = useState<SpreadsheetRow[]>(
    Array.from({ length: 50 }, () => ({
      id: uuidv4(),
      account: '',
      businessAccount: '',
      postContentA: '',
      postContentB: '',
      postContentC: '',
      label: '',
    }))
  );

  const [statusMessage, setStatusMessage] = useState('');
  const [sortConfig, setSortConfig] = useState<{ field: keyof SpreadsheetRow; direction: 'asc' | 'desc' } | null>(null);

  // Function to sort rows by a specified field
  const sortRows = (field: keyof SpreadsheetRow) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.field === field && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    const sortedRows = [...rows].sort((a, b) => {
      if (a[field] < b[field]) return direction === 'asc' ? -1 : 1;
      if (a[field] > b[field]) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    setRows(sortedRows);
    setSortConfig({ field, direction });
  };

  const getSortIndicator = (field: keyof SpreadsheetRow) => {
    if (!sortConfig || sortConfig.field !== field) return '';
    return sortConfig.direction === 'asc' ? '▲' : '▼';
  };

  // Function to export data to CSV
  const exportToCSV = () => {
    const csvContent = rows.map((row: SpreadsheetRow) =>
      `${row.account},${row.businessAccount},${row.label},${row.postContentA},${row.postContentB},${row.postContentC}`
    ).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'spreadsheet.csv');
    link.click();
  };

  // Function to export data to PDF
  const exportToPDF = () => {
    const doc = new jsPDF();
    let y = 10;
    rows.forEach((row: SpreadsheetRow) => {
      doc.text(`Account: ${row.account}, Business: ${row.businessAccount}, Label: ${row.label}, A: ${row.postContentA}, B: ${row.postContentB}, C: ${row.postContentC}`, 10, y);
      y += 10;
    });
    doc.save('spreadsheet.pdf');
  };

  // 各アカウントに対して投稿を行う関数
  const handlePost = async () => {
    try {
      await Promise.all(rows.map(row => {
        // 各投稿内容をアカウントに投稿
        return Promise.all([
          postToAccount(row.account, row.businessAccount, row.postContentA),
          postToAccount(row.account, row.businessAccount, row.postContentB),
          postToAccount(row.account, row.businessAccount, row.postContentC),
        ]);
      }));
      setStatusMessage('All posts were successful!'); // 成功メッセージを設定
    } catch (error: any) {
      console.error('Error during posting:', error);
      setStatusMessage('Some posts failed. Check the console for details.'); // エラーメッセージを設定
    }
  };

  // リプレイを検出し、自動返信を行う関数
  const handleAutoReply = () => {
    rows.forEach(row => {
      // 投稿内容Aに'reply'が含まれているかをチェック
      if (row.postContentA.includes('reply')) {
        autoReply('Thank you for your reply!'); // 定型文で返信
      }
    });
  };

  // 新しい行を追加する関数
  const addRow = () => {
    setRows([...rows, { id: uuidv4(), account: '', businessAccount: '', label: '', postContentA: '', postContentB: '', postContentC: '' }]);
  };

  // 行のデータを更新する関数
  const updateRow = (id: string, field: keyof SpreadsheetRow, value: string) => {
    const newRows = [...rows];
    const index = newRows.findIndex(row => row.id === id);
    if (index !== -1) {
      newRows[index][field] = value;
    }
    setRows(newRows);
  };

  // 行を削除する関数
  const deleteRow = (id: string) => {
    setRows(rows.filter(row => row.id !== id));
  };

  const find = () => {
    console.log('Find function executed');
  };

  return (
    <div>
      <div className="button-container">
        <button onClick={exportToPDF}>PDF</button>
        <button onClick={exportToCSV}>CSV</button>
        <button onClick={find}>検索</button>
        <button onClick={addRow}>行追加</button>
      </div>
      <p>{statusMessage}</p>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => sortRows('account')}>アカウント {getSortIndicator('account')}</th>
              <th onClick={() => sortRows('businessAccount')}>ビジ垢 {getSortIndicator('businessAccount')}</th>
              <th>投稿内容A</th>
              <th>投稿内容B</th>
              <th>投稿内容C</th>
              <th>投稿</th>
              <th>削除</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td><input value={row.account} onChange={(e) => updateRow(row.id, 'account', e.target.value)} /></td>
                <td><input value={row.businessAccount} onChange={(e) => updateRow(row.id, 'businessAccount', e.target.value)} /></td>
                <td><input value={row.postContentA} onChange={(e) => updateRow(row.id, 'postContentA', e.target.value)} /></td>
                <td><input value={row.postContentB} onChange={(e) => updateRow(row.id, 'postContentB', e.target.value)} /></td>
                <td><input value={row.postContentC} onChange={(e) => updateRow(row.id, 'postContentC', e.target.value)} /></td>
                <td>
                  <button onClick={() => {
                    postToAccount(row.account, row.businessAccount, row.postContentA);
                    postToAccount(row.account, row.businessAccount, row.postContentB);
                    postToAccount(row.account, row.businessAccount, row.postContentC);
                  }}>投稿</button>
                </td>
                <td>
                  <button onClick={() => deleteRow(row.id)}>行削除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SpreadSheet;
