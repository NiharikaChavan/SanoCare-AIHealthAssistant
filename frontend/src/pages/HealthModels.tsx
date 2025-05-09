import { useState } from 'react'
import HealthModelViewer from '../components/3d/HealthModelViewer'

const HealthModels = () => {
  const [selectedModel, setSelectedModel] = useState<'brain' | 'heart' | 'skeleton'>('brain')

  // These URLs should point to your actual 3D model files
  const modelUrls = {
    brain: '/models/brain.glb',
    heart: '/models/heart.glb',
    skeleton: '/models/skeleton.glb'
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Interactive Health Models</h1>
      
      <div className="mb-6">
        <div className="flex space-x-4">
          <button
            onClick={() => setSelectedModel('brain')}
            className={`px-4 py-2 rounded ${
              selectedModel === 'brain'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-800'
            }`}
          >
            Brain
          </button>
          <button
            onClick={() => setSelectedModel('heart')}
            className={`px-4 py-2 rounded ${
              selectedModel === 'heart'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-800'
            }`}
          >
            Heart
          </button>
          <button
            onClick={() => setSelectedModel('skeleton')}
            className={`px-4 py-2 rounded ${
              selectedModel === 'skeleton'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-800'
            }`}
          >
            Skeleton
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <HealthModelViewer
          modelUrl={modelUrls[selectedModel]}
          modelType={selectedModel}
          backgroundColor="#f8fafc"
        />
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">How to Interact</h2>
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          <li>Click and drag to rotate the model</li>
          <li>Scroll to zoom in and out</li>
          <li>Right-click and drag to pan</li>
        </ul>
      </div>
    </div>
  )
}

export default HealthModels 