import React, {createContext, useReducer, useContext, useMemo, type PropsWithChildren} from 'react';
import { type IWorkbookData } from '@univerjs/core';
import type {Operation} from "../types/contract.tsx";

type State = {
  workbook: IWorkbookData | null;
  pendingOps: Operation[];
};

type Action =
  | { type: 'REPLACE_WORKBOOK'; wb: IWorkbookData }
  | { type: 'QUEUE_OPS'; ops: Operation[] }
  | { type: 'CLEAR_PENDING' };

const WorkbookCtx = createContext<
  { state: State; dispatch: React.Dispatch<Action> } | undefined
>(undefined);

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'REPLACE_WORKBOOK':
      return { ...state, workbook: action.wb };

    case 'QUEUE_OPS':
      return { ...state, pendingOps: action.ops };

    case 'CLEAR_PENDING':
      return { ...state, pendingOps: [] };

    default:
      return state;
  }
}

export function WorkbookProvider({ children }: PropsWithChildren<object>) {
  const [state, dispatch] = useReducer(reducer, {
    workbook: null,
    pendingOps: [],
  });
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return <WorkbookCtx.Provider value={value}>{children}</WorkbookCtx.Provider>;
}

export function useWorkbook() {
  const ctx = useContext(WorkbookCtx);
  if (!ctx) throw new Error('useWorkbook must be in <WorkbookProvider>');
  return ctx;
}