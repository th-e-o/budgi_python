import {useState, useEffect, useRef, useCallback} from 'react';
import {blobToText} from '../Helpers/blobToText';
import type {ClientMessage, ServerMessage} from "../types/contract.tsx";

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

let wsInstance: WebSocket | null = null;
let workerInstance: Worker | null = null;
let connectionPromise: Promise<void> | null = null;

function setupConnection(
    onMessage: (msg: ServerMessage) => void,
    onStatusChange: (status: ConnectionStatus) => void
): Promise<void> {
    if (connectionPromise) {
        return connectionPromise;
    }

    connectionPromise = new Promise((resolve, reject) => {
        // Initialize Web Worker for stringifying JSON
        workerInstance = new Worker('/json-stringifier.worker.js');
        console.log("JSON Stringifier Web Worker initialized.");

        workerInstance.onmessage = (event) => {
            const jsonString = event.data;
            if (wsInstance?.readyState === WebSocket.OPEN) {
                wsInstance.send(jsonString);
            }
        };

        // Determine WebSocket URL
        let wsUrl;
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
        if (API_BASE_URL) {
            const wsHost = API_BASE_URL.replace(/^http/, 'ws');
            wsUrl = `${wsHost}/ws`;
        } else {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl = `${wsProtocol}//${window.location.host}${window.location.pathname}ws`;
        }
        console.log(`Connecting WebSocket to: ${wsUrl}`);
        wsInstance = new WebSocket(wsUrl);

        wsInstance.onopen = () => {
            console.log('WebSocket connected');
            onStatusChange('connected');
            resolve();
        };

        wsInstance.onclose = () => {
            console.log('WebSocket disconnected');
            onStatusChange('disconnected');
            // Clean up singleton instances on final close
            wsInstance = null;
            workerInstance?.terminate();
            workerInstance = null;
            connectionPromise = null;
        };

        wsInstance.onerror = (err) => {
            console.error('WebSocket error:', err);
            onStatusChange('disconnected');
            reject(err);
        };

        wsInstance.onmessage = async (evt) => {
            const msg: ServerMessage = JSON.parse(await blobToText(evt.data));
            console.log('Received WebSocket message:', msg);
            onMessage(msg);
        };
    });

    return connectionPromise;
}

export function useAppWebSocket() {
    const [lastMessage, setLastMessage] = useState<ServerMessage | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
    const isMounted = useRef(true);

    useEffect(() => {
        isMounted.current = true;

        // Handlers that update the component's state
        const handleStatusChange = (status: ConnectionStatus) => {
            if (isMounted.current) setConnectionStatus(status);
        };
        const handleMessage = (msg: ServerMessage) => {
            if (isMounted.current) setLastMessage(msg);
        };

        // Only try to set up if no connection is active or pending
        if (!wsInstance && !connectionPromise) {
            setupConnection(handleMessage, handleStatusChange);
        } else {
            // If connection already exists, just sync status
            if (wsInstance?.readyState === WebSocket.OPEN) {
                setConnectionStatus('connected');
            }
        }

        return () => {
            isMounted.current = false;
            // The actual cleanup of the WebSocket is now handled by the `onclose` event
            // to prevent StrictMode from killing it prematurely.
            console.log("React component unmounted, but WebSocket connection persists.");
        };
    }, []);

    const sendMessage = useCallback(<T extends ClientMessage['type']>(
        type: T,
        payload: Extract<ClientMessage, { type: T }>['payload']
    ) => {
        // Now read from the singleton instances
        if (wsInstance?.readyState !== WebSocket.OPEN || !workerInstance) {
            console.warn('Cannot send message: WebSocket not connected or worker not ready.');
            return;
        }
        const message = {type, payload};
        workerInstance.postMessage(message);
    }, []); // No dependency needed as it reads from module-level singletons

    return {connectionStatus, lastMessage, sendMessage};
}