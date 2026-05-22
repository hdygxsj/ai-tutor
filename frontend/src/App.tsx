import { useCallback, useEffect, useState } from "react";

import { AppShell } from "./components/AppShell";
import {
  APP_ROUTE_BY_KEY,
  type AppMenuKey,
  resolveAppRoute,
} from "./app-routes";

export default function App() {
  const [currentRoute, setCurrentRoute] = useState(() =>
    resolveRouteFromLocation({ replaceInvalidPath: true }),
  );

  useEffect(() => {
    function handlePopState() {
      setCurrentRoute(resolveRouteFromLocation({ replaceInvalidPath: true }));
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const handleSelect = useCallback(
    (key: AppMenuKey) => {
      const route = APP_ROUTE_BY_KEY[key];

      if (route.path !== window.location.pathname) {
        window.history.pushState(null, "", route.path);
      }

      setCurrentRoute(route);
    },
    [],
  );

  return (
    <AppShell activeKey={currentRoute.key} onSelect={handleSelect}>
      {currentRoute.element}
    </AppShell>
  );
}

function resolveRouteFromLocation({ replaceInvalidPath }: { replaceInvalidPath: boolean }) {
  const { route, shouldReplace } = resolveAppRoute(window.location.pathname);

  if (replaceInvalidPath && shouldReplace) {
    window.history.replaceState(null, "", route.path);
  }

  return route;
}
