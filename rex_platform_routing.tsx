import React from 'react';
import { ArrowDown, ArrowRight, Phone, FileText, Users } from 'lucide-react';

const CaseRoutingDiagram = () => {
  return (
    <div className="w-full max-w-[1800px] mx-auto p-8 bg-gradient-to-br from-blue-50 to-indigo-50">
      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        REC/Platform Case Routing Flow
      </h1>
      
      {/* Starting Point */}
      <div className="flex justify-center mb-6">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg shadow-xl px-8 py-4">
          <h2 className="text-2xl font-bold text-center">All REC/Platform Cases</h2>
          <p className="text-center text-sm mt-1">(REX or RCCC ownership doesn't matter)</p>
        </div>
      </div>
      
      <div className="flex justify-center mb-8">
        <ArrowDown className="w-8 h-8 text-indigo-600" />
      </div>
      
      {/* First Decision Point */}
      <div className="flex justify-center mb-8">
        <div className="bg-yellow-100 border-4 border-yellow-500 rounded-lg shadow-lg px-8 py-4">
          <h3 className="text-xl font-bold text-center text-yellow-800">Is this a NEW or OLD case?</h3>
        </div>
      </div>
      
      <div className="flex justify-center gap-32 mb-8">
        <div className="flex flex-col items-center">
          <ArrowDown className="w-8 h-8 text-orange-500 mb-2" />
          <span className="font-bold text-orange-600 text-lg">OLD BACKLOG</span>
        </div>
        <div className="flex flex-col items-center">
          <ArrowDown className="w-8 h-8 text-green-500 mb-2" />
          <span className="font-bold text-green-600 text-lg">NEW INCOMING</span>
        </div>
      </div>
      
      {/* Two Main Paths */}
      <div className="grid grid-cols-2 gap-12">
        
        {/* LEFT PATH - OLD BACKLOG */}
        <div className="bg-orange-50 rounded-xl p-6 border-4 border-orange-300">
          <div className="bg-orange-500 text-white rounded-lg p-3 mb-6">
            <h3 className="text-xl font-bold text-center">OLD BACKLOG PATH</h3>
          </div>
          
          {/* Step 1 */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <div className="flex items-center mb-2">
              <div className="bg-orange-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">1</div>
              <h4 className="font-bold text-gray-800">Check Support Type</h4>
            </div>
            <p className="text-sm text-gray-600 ml-11">Is it Standard or Paid?</p>
          </div>
          
          <div className="flex justify-center my-3">
            <ArrowDown className="w-6 h-6 text-orange-500" />
          </div>
          
          {/* Standard and Paid Side by Side */}
          <div className="grid grid-cols-2 gap-3">
            {/* Step 2A - Standard */}
            <div className="bg-blue-100 rounded-lg shadow-md p-4 border-2 border-blue-400">
              <div className="flex items-center mb-2">
                <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-2">2A</div>
                <h4 className="font-bold text-blue-800 text-sm">Standard</h4>
              </div>
              <div className="ml-2">
                <p className="text-xs font-semibold text-gray-700 mb-1">Route to:</p>
                <p className="text-xs text-gray-800 font-medium">T2 or T3 REX/Platform</p>
                <p className="text-xs text-gray-600 mt-2 bg-white rounded p-2">
                  ✓ Controlled distribution<br/>
                  ✓ Coordinate with managers<br/>
                  ✓ India T2 & T3 standby (Mon)
                </p>
              </div>
            </div>
            
            {/* Step 2B - Paid */}
            <div className="bg-purple-100 rounded-lg shadow-md p-4 border-2 border-purple-400">
              <div className="flex items-center mb-2">
                <div className="bg-purple-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-2">2B</div>
                <h4 className="font-bold text-purple-800 text-sm">Paid</h4>
              </div>
              <div className="ml-2">
                <p className="text-xs font-semibold text-gray-700 mb-1">Route to:</p>
                <p className="text-xs text-gray-800 font-medium">REX ASE or T3 REX/Platform</p>
                <p className="text-xs text-gray-600 mt-2 bg-white rounded p-2">
                  ✓ Controlled distribution<br/>
                  ✓ Coordinate with managers<br/>
                  ✓ US & MNL moved to REX
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* RIGHT PATH - NEW INCOMING */}
        <div className="bg-green-50 rounded-xl p-6 border-4 border-green-300">
          <div className="bg-green-500 text-white rounded-lg p-3 mb-6">
            <h3 className="text-xl font-bold text-center">NEW INCOMING PATH</h3>
          </div>
          
          {/* Step 1 */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <div className="flex items-center mb-2">
              <div className="bg-green-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold mr-3">1</div>
              <h4 className="font-bold text-gray-800">Check Support Type</h4>
            </div>
            <p className="text-sm text-gray-600 ml-11">Standard or Paid?</p>
          </div>
          
          <div className="flex justify-center my-3">
            <ArrowDown className="w-6 h-6 text-green-500" />
          </div>
          
          {/* Standard and Paid Side by Side */}
          <div className="grid grid-cols-2 gap-3">
            {/* Standard Support Branch */}
            <div>
              <div className="bg-blue-200 rounded-lg p-2 mb-3">
                <h4 className="font-bold text-blue-800 text-center text-sm">STANDARD</h4>
              </div>
              
              {/* Step 2A */}
              <div className="bg-white rounded-lg shadow-md p-3 mb-3">
                <div className="flex items-center mb-2">
                  <div className="bg-green-500 text-white rounded-full w-7 h-7 flex items-center justify-center font-bold text-sm mr-2">2</div>
                  <h4 className="font-bold text-gray-800 text-xs">Entry Method?</h4>
                </div>
              </div>
              
              <div className="flex justify-center my-2">
                <ArrowDown className="w-4 h-4 text-green-500" />
              </div>
              
              {/* Call Option */}
              <div className="bg-cyan-100 rounded-lg shadow-md p-2 mb-2 border-2 border-cyan-400">
                <div className="flex items-center mb-1">
                  <Phone className="w-3 h-3 text-cyan-600 mr-1" />
                  <div className="bg-cyan-500 text-white rounded-full w-6 h-6 flex items-center justify-center font-bold text-xs mr-1">3A</div>
                  <h4 className="font-semibold text-cyan-800 text-xs">Call</h4>
                </div>
                <div className="ml-1">
                  <p className="text-xs text-gray-800">→ Engineer taking call</p>
                  <p className="text-xs text-gray-600 mt-1 bg-white rounded p-1">
                    1. Triage<br/>
                    2. Transfer if needed<br/>
                    3. Confirm w/ customer
                  </p>
                </div>
              </div>
              
              <div className="text-center text-gray-400 text-xs my-1">OR</div>
              
              {/* Online Option */}
              <div className="bg-teal-100 rounded-lg shadow-md p-2 border-2 border-teal-400">
                <div className="flex items-center mb-1">
                  <FileText className="w-3 h-3 text-teal-600 mr-1" />
                  <div className="bg-teal-500 text-white rounded-full w-6 h-6 flex items-center justify-center font-bold text-xs mr-1">3B</div>
                  <h4 className="font-semibold text-teal-800 text-xs">Online</h4>
                </div>
                <div className="ml-1">
                  <p className="text-xs text-gray-800">→ REX T2/SME</p>
                  <p className="text-xs text-gray-600 mt-1 bg-white rounded p-1">
                    Auto-routes to REX T2/SME
                  </p>
                </div>
              </div>
            </div>
            
            {/* Paid Support Branch */}
            <div>
              <div className="bg-purple-200 rounded-lg p-2 mb-3">
                <h4 className="font-bold text-purple-800 text-center text-sm">PAID</h4>
              </div>
              
              {/* All Paid Goes to Same Place */}
              <div className="bg-purple-100 rounded-lg shadow-md p-3 border-2 border-purple-400">
                <div className="flex items-center mb-2">
                  <div className="bg-purple-500 text-white rounded-full w-7 h-7 flex items-center justify-center font-bold text-sm mr-2">2</div>
                  <h4 className="font-bold text-purple-800 text-xs">All Methods</h4>
                </div>
                <div className="ml-1">
                  <p className="text-xs font-semibold text-gray-700 mb-1">Route to:</p>
                  <p className="text-xs text-gray-800 font-medium">→ REX ASE or T3 REX/Platform</p>
                  <p className="text-xs text-gray-600 mt-2 bg-white rounded p-2">
                    Direct routing regardless of call or online
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bottom Summary */}
      <div className="mt-8 bg-white rounded-lg shadow-lg p-6 border-t-4 border-indigo-500">
        <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center">
          <Users className="w-5 h-5 mr-2 text-indigo-600" />
          Key Takeaways
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start">
            <span className="text-2xl mr-2">📊</span>
            <span className="text-gray-700"><strong>Old backlog:</strong> Controlled distribution with manager coordination</span>
          </div>
          <div className="flex items-start">
            <span className="text-2xl mr-2">⚡</span>
            <span className="text-gray-700"><strong>New cases:</strong> Automatic routing based on entry method</span>
          </div>
          <div className="flex items-start">
            <span className="text-2xl mr-2">🎯</span>
            <span className="text-gray-700"><strong>All cases:</strong> REX/RCCC ownership doesn't affect routing</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CaseRoutingDiagram;