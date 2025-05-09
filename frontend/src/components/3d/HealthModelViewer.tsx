import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF } from '@react-three/drei'
import { Suspense } from 'react'
import * as THREE from 'three'

// Loader component for showing loading state
const Loader = () => {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  )
}

// Model component
const Model = ({ url }: { url: string }) => {
  const { scene } = useGLTF(url)
  
  return (
    <primitive 
      object={scene} 
      scale={1} 
      position={[0, 0, 0]}
    />
  )
}

// Main viewer component
const HealthModelViewer = ({ 
  modelUrl, 
  modelType = 'brain',
  backgroundColor = '#ffffff'
}: { 
  modelUrl: string
  modelType?: 'brain' | 'heart' | 'skeleton'
  backgroundColor?: string
}) => {
  return (
    <div className="w-full h-[500px] relative">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        style={{ background: backgroundColor }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
          <Model url={modelUrl} />
          <OrbitControls 
            enableZoom={true}
            enablePan={true}
            enableRotate={true}
            minDistance={2}
            maxDistance={10}
          />
        </Suspense>
      </Canvas>
    </div>
  )
}

export default HealthModelViewer 