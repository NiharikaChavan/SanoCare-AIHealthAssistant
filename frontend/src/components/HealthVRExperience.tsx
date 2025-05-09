import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF, Environment, PresentationControls } from '@react-three/drei';
import { Heart, Brain, Lungs, Bone, Muscle } from 'lucide-react';

// 3D Model Loader Component
function Model({ url, position = [0, 0, 0] }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} position={position} />;
}

// Interactive Body System Component
function BodySystem({ system, position, icon: Icon, color }) {
  const [hovered, setHovered] = useState(false);
  
  return (
    <group position={position}>
      <mesh
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial 
          color={hovered ? color : 'white'} 
          transparent 
          opacity={0.8}
        />
      </mesh>
      <Icon 
        size={24} 
        color={hovered ? color : 'white'} 
        style={{ position: 'absolute', transform: 'translate(-50%, -50%)' }}
      />
    </group>
  );
}

const HealthVRExperience: React.FC = () => {
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);

  return (
    <div className="relative w-full h-screen bg-gradient-to-b from-slate-900 to-blue-900">
      {/* 3D Canvas */}
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <Suspense fallback={null}>
          <Environment preset="city" />
          <PresentationControls
            global
            config={{ mass: 2, tension: 500 }}
            snap={{ mass: 4, tension: 1500 }}
            rotation={[0, 0, 0]}
            polar={[-Math.PI / 3, Math.PI / 3]}
            azimuth={[-Math.PI / 1.4, Math.PI / 2]}
          >
            <group>
              {/* Human Body Model */}
              <Model url="/models/human_body.glb" />
              
              {/* Interactive Systems */}
              <BodySystem 
                system="circulatory" 
                position={[-1, 1, 0]} 
                icon={Heart} 
                color="#ef4444"
              />
              <BodySystem 
                system="nervous" 
                position={[1, 1, 0]} 
                icon={Brain} 
                color="#3b82f6"
              />
              <BodySystem 
                system="respiratory" 
                position={[-1, -1, 0]} 
                icon={Lungs} 
                color="#10b981"
              />
              <BodySystem 
                system="skeletal" 
                position={[1, -1, 0]} 
                icon={Bone} 
                color="#f59e0b"
              />
              <BodySystem 
                system="muscular" 
                position={[0, 0, 1]} 
                icon={Muscle} 
                color="#8b5cf6"
              />
            </group>
          </PresentationControls>
        </Suspense>
        <OrbitControls enableZoom={false} />
      </Canvas>

      {/* Overlay UI */}
      <div className="absolute bottom-0 left-0 right-0 p-8 bg-black/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-4">
            Interactive Health Education
          </h2>
          <p className="text-slate-300 mb-6">
            Explore different body systems and learn about their functions and common health conditions.
          </p>
          <div className="grid grid-cols-5 gap-4">
            {['Circulatory', 'Nervous', 'Respiratory', 'Skeletal', 'Muscular'].map((system) => (
              <button
                key={system}
                onClick={() => setSelectedSystem(system.toLowerCase())}
                className="p-4 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              >
                <span className="text-white font-medium">{system}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* System Information Panel */}
      {selectedSystem && (
        <div className="absolute top-0 right-0 w-96 h-full bg-slate-900/90 backdrop-blur-sm p-6 overflow-y-auto">
          <h3 className="text-xl font-bold text-white mb-4">
            {selectedSystem.charAt(0).toUpperCase() + selectedSystem.slice(1)} System
          </h3>
          <div className="space-y-4">
            <div className="bg-slate-800/50 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Key Functions</h4>
              <p className="text-slate-300">
                {/* Add system-specific information here */}
              </p>
            </div>
            <div className="bg-slate-800/50 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Common Conditions</h4>
              <ul className="text-slate-300 list-disc list-inside">
                {/* Add system-specific conditions here */}
              </ul>
            </div>
            <div className="bg-slate-800/50 p-4 rounded-lg">
              <h4 className="text-white font-medium mb-2">Health Tips</h4>
              <p className="text-slate-300">
                {/* Add system-specific health tips here */}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthVRExperience; 