import React from "react";

export const TradingTerminal: React.FC = () => {
    return (
        <div className="h-screen bg-gray-900 text-white p-4">
            <h1 className="text-2xl font-bold text-cyan-400 mb-4">REZTRADER Terminal</h1>
            <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg">
                    <h2 className="text-sm text-gray-400">Exchange Matrix</h2>
                    <div className="mt-2 text-white">BINANCE: $52,341</div>
                </div>
                <div className="bg-gray-800 p-4 rounded-lg col-span-2">
                    <h2 className="text-sm text-gray-400">Live Arbitrage</h2>
                    <p className="text-gray-300 mt-2">Waiting for data...</p>
                </div>
            </div>
        </div>
    );
};

