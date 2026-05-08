// frontend/src/components/network/ConnectionGraph.jsx
import { useEffect, useCallback } from 'react'
import { useNetworkStore } from '../../store/networkStore'
import { truncate } from '../../utils/formatters'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

const processNodeStyle = {
  background:   '#00d4ff15',
  border:       '1px solid #00d4ff55',
  borderRadius: '8px',
  padding:      '8px 14px',
  color:        '#00d4ff',
  fontSize:     '11px',
  fontFamily:   'monospace',
  minWidth:     '120px',
  textAlign:    'center',
}

const domainNodeStyle = {
  background:   '#00ff8815',
  border:       '1px solid #00ff8855',
  borderRadius: '8px',
  padding:      '8px 14px',
  color:        '#00ff88',
  fontSize:     '11px',
  fontFamily:   'monospace',
  minWidth:     '140px',
  textAlign:    'center',
}

const flaggedDomainStyle = {
  ...domainNodeStyle,
  background: '#ff444415',
  border:     '1px solid #ff444455',
  color:      '#ff4444',
}

export function ConnectionGraph() {
  const connections = useNetworkStore(s => s.connections)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const buildGraph = useCallback(() => {
    const processMap = new Map()   // procId → index
    const domainMap  = new Map()   // domainId → index
    const newNodes   = []
    const newEdges   = []
    const seenEdges  = new Set()

    const sample = connections.slice(0, 40)

    sample.forEach((conn) => {
      const procLabel  = `${conn.process_name || 'unknown'}\nPID ${conn.pid}`
      const procId     = `proc_${conn.pid}`
      const domainLabel = conn.domain || conn.remote_addr || 'unknown'
      const domainId   = `dom_${(conn.domain || conn.remote_addr || 'x').replace(/[^a-zA-Z0-9]/g, '_')}`

      if (!processMap.has(procId)) {
        const idx = processMap.size
        processMap.set(procId, idx)
        newNodes.push({
          id:       procId,
          data:     { label: truncate(procLabel, 22) },
          position: { x: 60, y: 80 + idx * 80 },
          style:    processNodeStyle,
          draggable: true,
        })
      }

      if (!domainMap.has(domainId)) {
        const idx = domainMap.size
        domainMap.set(domainId, idx)
        newNodes.push({
          id:       domainId,
          data:     { label: truncate(domainLabel, 28) },
          position: { x: 380, y: 60 + idx * 65 },
          style:    conn.flagged ? flaggedDomainStyle : domainNodeStyle,
          draggable: true,
        })
      }

      const edgeId = `${procId}__${domainId}`
      if (!seenEdges.has(edgeId)) {
        seenEdges.add(edgeId)
        newEdges.push({
          id:       edgeId,
          source:   procId,
          target:   domainId,
          animated: conn.flagged,
          style: {
            stroke:      conn.flagged ? '#ff4444' : '#00d4ff44',
            strokeWidth: conn.flagged ? 2 : 1,
          },
        })
      }
    })

    setNodes(newNodes)
    setEdges(newEdges)
  }, [connections, setNodes, setEdges])

  useEffect(() => {
    buildGraph()
  }, [buildGraph])

  if (connections.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-sentinel-muted text-sm">
        <div className="text-center space-y-2">
          <p className="text-3xl">🌐</p>
          <p>No connections tracked yet</p>
          <p className="text-xs">Browse some websites — connections will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        height:       400,
        background:   '#0a0e1a',
        borderRadius: 8,
        overflow:     'hidden',
        border:       '1px solid #1f2937',
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={2}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          color="#1f2937"
          gap={20}
          size={1}
        />
        <Controls
          style={{
            background: '#111827',
            border:     '1px solid #1f2937',
            borderRadius: 6,
          }}
        />
        <MiniMap
          style={{
            background:   '#111827',
            border:       '1px solid #1f2937',
            borderRadius: 6,
          }}
          nodeColor={(n) =>
            n.style?.color === '#ff4444' ? '#ff4444' :
            n.style?.color === '#00d4ff' ? '#00d4ff' : '#00ff88'
          }
          maskColor="#0a0e1a99"
        />
      </ReactFlow>
    </div>
  )
}