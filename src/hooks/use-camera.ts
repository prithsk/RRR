import { useCameraPermissions } from 'expo-camera';

/** Thin wrapper around expo-camera permissions for the capture flow. */
export function useCamera() {
  const [permission, requestPermission] = useCameraPermissions();

  return {
    permission,
    requestPermission,
    granted: permission?.granted ?? false,
    canAskAgain: permission?.canAskAgain ?? true,
  };
}
