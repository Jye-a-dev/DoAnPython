import * as React from "react";

/**
 * Returns true once the component has mounted on the client.
 * Used to avoid SSR hydration mismatches when rendering client-only UI.
 */
export function useMounted(): boolean {
  return React.useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

