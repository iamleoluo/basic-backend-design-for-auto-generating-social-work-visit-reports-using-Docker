# 🌳 FamilyTree.js 整合指南

## 📋 概述

已成功整合 FamilyTree.js 專用於家庭關係圖，與 vis.js 人物關係圖形成雙圖表架構：

- **人物關係圖**: 使用 vis.js，專注個人和人際關係網絡
- **家庭關係圖**: 使用 FamilyTree.js，專注家族樹和血緣關係

## 🔧 後端配置已完成

### ✅ 已修改的配置文件

1. **family_graph.json**: 輸出 FamilyTree.js 兼容格式
2. **family_graph_chat.json**: 專門的家族樹編輯對話
3. **graph_routes.py**: API 自動路由到正確配置

### 📊 FamilyTree.js 數據格式

```json
[
  {
    "id": 1,
    "name": "案主",
    "gender": "female",
    "birth_year": "1988",
    "pids": [2],
    "mid": 3,
    "fid": 4,
    "tags": ["主要當事人"]
  },
  {
    "id": 2,
    "name": "配偶",
    "gender": "male",
    "birth_year": "1985",
    "pids": [1],
    "tags": ["配偶"]
  }
]
```

### 🔑 字段說明

- `id`: 唯一識別碼（數字）
- `name`: 姓名或稱謂
- `gender`: 性別 ("male"/"female")
- `birth_year`: 出生年份（可選）
- `pids`: 配偶ID陣列（已婚關係）
- `mid`: 母親ID（親子關係）
- `fid`: 父親ID（親子關係）
- `tags`: 標籤陣列（角色、特徵等）

## 🌐 前端整合步驟

### 1. 安裝FamilyTree.js

```bash
npm install @balkangraph/familytree.js
```

### 2. 組件架構建議

```javascript
// GraphContainer.jsx
import React from 'react';
import PersonGraph from './PersonGraph';    // 使用 vis.js
import FamilyGraph from './FamilyGraph';    // 使用 FamilyTree.js

const GraphContainer = ({ graphType, data }) => {
  return (
    <div className="graph-container">
      {graphType === 'person' ? (
        <PersonGraph data={data} />
      ) : (
        <FamilyGraph data={data} />
      )}
    </div>
  );
};
```

### 3. FamilyTree.js 組件實現

```javascript
// FamilyGraph.jsx
import React, { useEffect, useRef } from 'react';
import FamilyTree from '@balkangraph/familytree.js';

const FamilyGraph = ({ data }) => {
  const divRef = useRef();

  useEffect(() => {
    if (data && divRef.current) {
      const family = new FamilyTree(divRef.current, {
        nodes: data,
        // 自定義樣式
        template: "hugo",
        nodeBinding: {
          field_0: "name",
          field_1: "tags",
          img_0: "img"
        },
        // 中文化設定
        editForm: {
          titleBinding: "name",
          photoBinding: "img",
          addMore: "添加更多",
          addMoreBtn: "添加",
          addMoreFieldName: "名稱"
        }
      });
    }
  }, [data]);

  return <div ref={divRef} style={{width: '100%', height: '600px'}} />;
};

export default FamilyGraph;
```

### 4. API 調用保持不變

```javascript
// 現有的 API 調用無需修改
const response = await fetch('/api/PersonGraph', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: transcript,
    graphType: 'family'  // 關鍵參數
  })
});
```

## 🎨 樣式自定義

### FamilyTree.js 模板選項

```javascript
// 可用模板
const templates = [
  "base",     // 基本模板
  "hugo",     // 現代風格
  "olivia",   // 簡潔風格
  "belinda",  // 專業風格
  "rony"      // 圓形風格
];

// 自定義樣式
const config = {
  template: "hugo",
  orientation: FamilyTree.orientation.top,
  nodeBinding: {
    field_0: "name",
    field_1: "tags",
    field_2: "birth_year"
  }
};
```

### CSS 自定義

```css
/* 家族樹容器 */
.family-tree-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

/* 節點樣式 */
.node {
  cursor: pointer;
  transition: all 0.3s ease;
}

.node:hover {
  transform: scale(1.05);
}
```

## 🔄 對話功能整合

```javascript
// 家族樹對話 API
const editFamilyTree = async (message, currentGraph) => {
  const response = await fetch('/api/PersonGraphChat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      currentGraph: JSON.stringify(currentGraph),
      graphType: 'family'  // 使用家族樹專用對話
    })
  });
  
  return response.body.getReader();
};
```

## 📱 響應式設計

```javascript
// 響應式配置
const getResponsiveConfig = () => {
  const isMobile = window.innerWidth < 768;
  
  return {
    scaleInitial: isMobile ? 0.5 : 1,
    template: isMobile ? "base" : "hugo",
    orientation: isMobile ? 
      FamilyTree.orientation.top : 
      FamilyTree.orientation.top,
    nodeBinding: {
      field_0: "name",
      field_1: isMobile ? undefined : "tags"
    }
  };
};
```

## 🧪 測試建議

### 單元測試

```javascript
// FamilyGraph.test.jsx
import { render } from '@testing-library/react';
import FamilyGraph from './FamilyGraph';

test('renders family tree with data', () => {
  const mockData = [
    { id: 1, name: "測試人員", gender: "male" }
  ];
  
  render(<FamilyGraph data={mockData} />);
  // 測試渲染邏輯
});
```

### API 測試

```javascript
// 測試後端 API
const testFamilyGraphAPI = async () => {
  const response = await fetch('/api/PersonGraph', {
    method: 'POST',
    body: JSON.stringify({
      text: "測試家庭",
      graphType: 'family'
    })
  });
  
  const data = await response.json();
  console.log('FamilyTree format:', data);
};
```

## 🚀 完整實現範例

```javascript
// App.jsx
import React, { useState } from 'react';
import GraphContainer from './components/GraphContainer';

const App = () => {
  const [graphType, setGraphType] = useState('person');
  const [graphData, setGraphData] = useState(null);

  const generateGraph = async (transcript) => {
    const response = await fetch('/api/PersonGraph', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: transcript,
        graphType: graphType  // 'person' 或 'family'
      })
    });

    const data = await response.json();
    setGraphData(data);
  };

  return (
    <div className="app">
      <div className="controls">
        <button 
          onClick={() => setGraphType('person')}
          className={graphType === 'person' ? 'active' : ''}
        >
          人物關係圖 (vis.js)
        </button>
        <button 
          onClick={() => setGraphType('family')}
          className={graphType === 'family' ? 'active' : ''}
        >
          家庭關係圖 (FamilyTree.js)
        </button>
      </div>
      
      <GraphContainer 
        graphType={graphType} 
        data={graphData} 
      />
    </div>
  );
};

export default App;
```

## 🎯 完成狀態

✅ **後端配置完成**
- FamilyTree.js 格式輸出
- 專用家族樹對話配置
- API 自動路由切換

✅ **整合指南完成**
- 詳細實現步驟
- 樣式自定義選項
- 響應式設計建議

🎉 **現在可以開始前端整合工作！**