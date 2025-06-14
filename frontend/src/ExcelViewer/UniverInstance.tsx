import { FUniver } from '@univerjs/presets';

let api: FUniver | null = null;
export const setUniverAPI = (u: FUniver) => (api = u);
export const getUniverAPI = () => api;