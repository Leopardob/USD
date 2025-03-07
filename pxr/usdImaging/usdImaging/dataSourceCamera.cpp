//
// Copyright 2022 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usdImaging/usdImaging/dataSourceCamera.h"
#include "pxr/usdImaging/usdImaging/dataSourceAttribute.h"

#include "pxr/imaging/hd/cameraSchema.h"

PXR_NAMESPACE_OPEN_SCOPE

namespace
{

template <typename T>
class _ScalingTypedSampledDataSource : public HdTypedSampledDataSource<T>
{
public:
    HD_DECLARE_DATASOURCE(_ScalingTypedSampledDataSource<T>);

    _ScalingTypedSampledDataSource(
        const typename HdTypedSampledDataSource<T>::Handle &dataSource,
            T scale)
    : _dataSource(dataSource)
    , _scale(scale)
    {
    }

    VtValue GetValue(HdSampledDataSource::Time shutterOffset) override
    {
        return VtValue(GetTypedValue(shutterOffset));
    }

    T GetTypedValue(HdSampledDataSource::Time shutterOffset) override
    {
        if (!_dataSource) {
            return 0.0f;
        }
        return _dataSource->GetTypedValue(shutterOffset) * _scale;
    }

    bool GetContributingSampleTimesForInterval(
            HdSampledDataSource::Time startTime,
            HdSampledDataSource::Time endTime,
            std::vector<HdSampledDataSource::Time> *outSampleTimes) override
    {
        if (!_dataSource) {
            return false;
        }
        return _dataSource->GetContributingSampleTimesForInterval(
                startTime, endTime, outSampleTimes);
    }

private:
    typename HdTypedSampledDataSource<T>::Handle _dataSource;
    T _scale;
};

class _Vec4fArrayToVec4dArrayDataSource
    : public HdTypedSampledDataSource<VtArray<GfVec4d>>
{
public:
    HD_DECLARE_DATASOURCE(_Vec4fArrayToVec4dArrayDataSource);
    
    _Vec4fArrayToVec4dArrayDataSource(
        const HdTypedSampledDataSource<VtArray<GfVec4f>>::Handle &dataSource)
    : _dataSource(dataSource)
    {
    }

    VtValue GetValue(HdSampledDataSource::Time shutterOffset) override
    {
        return VtValue(GetTypedValue(shutterOffset));
    }

    VtArray<GfVec4d> GetTypedValue(
        HdSampledDataSource::Time shutterOffset) override
    {
        VtArray<GfVec4d> result;
        if (!_dataSource) {
            return result;
        }
         
        const VtArray<GfVec4f> data =
            _dataSource->GetTypedValue(shutterOffset);
        result.resize(data.size());
        for (size_t i = 0; i < data.size(); ++i) {
            result[i] = GfVec4d(data[i]);
        }
        return result;
    }

    bool GetContributingSampleTimesForInterval(
            HdSampledDataSource::Time startTime,
            HdSampledDataSource::Time endTime,
            std::vector<HdSampledDataSource::Time> *outSampleTimes) override
    {
        if (!_dataSource) {
            return false;
        }

        return _dataSource->GetContributingSampleTimesForInterval(
                startTime, endTime, outSampleTimes);
    }

private:
    typename HdTypedSampledDataSource<VtArray<GfVec4f>>::Handle _dataSource;
};

class _CameraLinearExposureScaleDataSource
    : public HdTypedSampledDataSource<float>
{
public:
    HD_DECLARE_DATASOURCE(_CameraLinearExposureScaleDataSource);

    _CameraLinearExposureScaleDataSource(
        const SdfPath &sceneIndexPath,
        UsdGeomCamera usdCamera,
        const UsdImagingDataSourceStageGlobals &stageGlobals)
    : _sceneIndexPath(sceneIndexPath)
    , _usdCamera(usdCamera)
    , _stageGlobals(stageGlobals)
    {
        static const HdDataSourceLocator linearExposureScaleLocator = 
            HdCameraSchema::GetLinearExposureScaleLocator();

        static const std::vector<TfToken> inputNames = {
            UsdGeomTokens->exposure,
            UsdGeomTokens->exposureTime,
            UsdGeomTokens->exposureIso,
            UsdGeomTokens->exposureFStop,
            UsdGeomTokens->exposureResponsivity
        };

        _inputs.resize(inputNames.size());
        UsdPrim prim = _usdCamera.GetPrim();
        for (const TfToken& inputName : inputNames) {
            _inputs.push_back(UsdImagingDataSourceAttributeNew(
                prim.GetAttribute(inputName),
                _stageGlobals,
                _sceneIndexPath,
                linearExposureScaleLocator));
        }
    }

    VtValue GetValue(Time shutterOffset) override
    {
        return VtValue(GetTypedValue(shutterOffset));
    }

    float GetTypedValue(Time shutterOffset) override
    {
        UsdTimeCode time = _stageGlobals.GetTime();
        if (time.IsNumeric()) {
            time = UsdTimeCode(time.GetValue() + shutterOffset);
        }
        return _usdCamera.ComputeLinearExposureScale(time);
    }

    bool GetContributingSampleTimesForInterval(
        Time startTime,
        Time endTime,
        std::vector<Time> *outSampleTimes) override
    {
        return HdGetMergedContributingSampleTimesForInterval(
            _inputs.size(),
            _inputs.data(),
            startTime,
            endTime,
            outSampleTimes);
    }

private:
    const SdfPath _sceneIndexPath;
    UsdGeomCamera _usdCamera;
    const UsdImagingDataSourceStageGlobals & _stageGlobals;

    // Copies of the input attributes, for time-varyingness and time samples.
    std::vector<HdSampledDataSourceHandle> _inputs;
};

} // namespace anonymous

UsdImagingDataSourceCamera::UsdImagingDataSourceCamera(
        const SdfPath &sceneIndexPath,
        UsdGeomCamera usdCamera,
        const UsdImagingDataSourceStageGlobals &stageGlobals)
    : _sceneIndexPath(sceneIndexPath)
    , _usdCamera(usdCamera)
    , _stageGlobals(stageGlobals)
{
}

TfTokenVector
UsdImagingDataSourceCamera::GetNames()
{
    return
        UsdGeomCamera::GetSchemaAttributeNames(/* includeInherited = */ false);
}

HdDataSourceBaseHandle
UsdImagingDataSourceCamera::Get(const TfToken &name)
{
    if (name == HdCameraSchemaTokens->linearExposureScale) {
        return _CameraLinearExposureScaleDataSource::New(
            _sceneIndexPath, _usdCamera, _stageGlobals);
    }

    // Handle necessary schema name conversions.
    TfToken usdName = name;
    // UsdGeomTokens->shutterOpen is "shutter:open" and thus different
    // from the camera schema.
    if (name == HdCameraSchemaTokens->shutterOpen) {
        usdName = UsdGeomTokens->shutterOpen;
    }
    // Similar to shutterOpen.
    else if (name == HdCameraSchemaTokens->shutterClose) {
        usdName = UsdGeomTokens->shutterClose;
    }
    // Hydra "exposure" attribute maps unchanged to USD "exposure".
    // Other Hydra "exposure" attributes need to be mapped due to e.g.
    // "exposure:time" vs "exposureTime"
    else if (name == HdCameraSchemaTokens->exposureTime) {
        usdName = UsdGeomTokens->exposureTime;
    }
    else if (name == HdCameraSchemaTokens->exposureIso) {
        usdName = UsdGeomTokens->exposureIso;
    }
    else if (name == HdCameraSchemaTokens->exposureFStop) {
        usdName = UsdGeomTokens->exposureFStop;
    }
    else if (name == HdCameraSchemaTokens->exposureResponsivity) {
        usdName = UsdGeomTokens->exposureResponsivity;
    }

    // Grab the attribute
    UsdAttribute attr = _usdCamera.GetPrim().GetAttribute(usdName);
    if (!attr) {
        return nullptr;
    }
    HdSampledDataSourceHandle const dataSource =
        UsdImagingDataSourceAttributeNew(
            attr,
            _stageGlobals,
            _sceneIndexPath,
            HdCameraSchema::GetDefaultLocator().Append(name));

    // Handle necessary type/scale conversions.
    if ( name == UsdGeomTokens->horizontalAperture ||
         name == UsdGeomTokens->verticalAperture ||
         name == UsdGeomTokens->horizontalApertureOffset ||
         name == UsdGeomTokens->verticalApertureOffset) {        
        return _ScalingTypedSampledDataSource<float>::New(
            HdTypedSampledDataSource<float>::Cast(dataSource),
            float(GfCamera::APERTURE_UNIT));
    } else if (name == UsdGeomTokens->focalLength) {
        return _ScalingTypedSampledDataSource<float>::New(
            HdTypedSampledDataSource<float>::Cast(dataSource),
            float(GfCamera::FOCAL_LENGTH_UNIT));
    } else if (name == UsdGeomTokens->clippingPlanes) {
        return _Vec4fArrayToVec4dArrayDataSource::New(
            HdTypedSampledDataSource<VtArray<GfVec4f>>::Cast(dataSource));
    }
    
    return dataSource;
}

// ----------------------------------------------------------------------------

UsdImagingDataSourceCameraPrim::UsdImagingDataSourceCameraPrim(
        const SdfPath &sceneIndexPath,
        UsdPrim usdPrim,
        const UsdImagingDataSourceStageGlobals &stageGlobals)
    : UsdImagingDataSourcePrim(sceneIndexPath, usdPrim, stageGlobals)
{
}

TfTokenVector 
UsdImagingDataSourceCameraPrim::GetNames()
{
    TfTokenVector result = UsdImagingDataSourcePrim::GetNames();
    result.push_back(HdCameraSchema::GetSchemaToken());
    return result;
}

HdDataSourceBaseHandle 
UsdImagingDataSourceCameraPrim::Get(const TfToken & name)
{
    if (name == HdCameraSchema::GetSchemaToken()) {
        return UsdImagingDataSourceCamera::New(
                _GetSceneIndexPath(),
                UsdGeomCamera(_GetUsdPrim()),
                _GetStageGlobals());
    } 

    return UsdImagingDataSourcePrim::Get(name);
}

HdDataSourceLocatorSet
UsdImagingDataSourceCameraPrim::Invalidate(
    UsdPrim const& prim,
    const TfToken &subprim,
    const TfTokenVector &properties,
    const UsdImagingPropertyInvalidationType invalidationType)
{
    TRACE_FUNCTION();

    HdDataSourceLocatorSet locators =
        UsdImagingDataSourcePrim::Invalidate(
            prim, subprim, properties, invalidationType);

    static TfTokenVector usdNames = 
        UsdGeomCamera::GetSchemaAttributeNames(/* includeInherited = */ false);

    for (const TfToken &propertyName : properties) {
        for (const TfToken &usdName : usdNames) {
            if (propertyName == usdName) {
                if (usdName == UsdGeomTokens->shutterOpen) {
                    // UsdGeomTokens->shutterOpen is "shutter:open" and thus
                    // different from camera schema.
                    locators.insert(
                        HdCameraSchema::GetShutterOpenLocator());
                } else if (usdName == UsdGeomTokens->shutterClose) {
                    // Similar to shutterOpen.
                    locators.insert(
                        HdCameraSchema::GetShutterCloseLocator());
                } else if (usdName == UsdGeomTokens->exposure) {
                    // "exposure" maps unchanged to "exposure", and is an input
                    // to the computed value stored at "linearExposureScale"
                    locators.insert(
                        HdCameraSchema::GetExposureLocator());
                    locators.insert(
                        HdCameraSchema::GetLinearExposureScaleLocator());
                } else if (usdName == UsdGeomTokens->exposureTime) {
                    // "exposure:time" maps to "exposureTime", and is an input
                    // to the computed value stored at "linearExposureScale"
                    locators.insert(
                        HdCameraSchema::GetExposureTimeLocator());
                    locators.insert(
                        HdCameraSchema::GetLinearExposureScaleLocator());
                } else if (usdName == UsdGeomTokens->exposureIso) {
                    // similar to exposureTime
                    locators.insert(
                        HdCameraSchema::GetExposureIsoLocator());
                    locators.insert(
                        HdCameraSchema::GetLinearExposureScaleLocator());
                } else if (usdName == UsdGeomTokens->exposureFStop) {
                    // similar to exposureTime
                    locators.insert(
                        HdCameraSchema::GetExposureFStopLocator());
                    locators.insert(
                        HdCameraSchema::GetLinearExposureScaleLocator());
                } else if (usdName == UsdGeomTokens->exposureResponsivity) {
                    // similar to exposureTime
                    locators.insert(
                        HdCameraSchema::GetExposureResponsivityLocator());
                    locators.insert(
                        HdCameraSchema::GetLinearExposureScaleLocator());
                } else {
                    locators.insert(
                        HdCameraSchema::GetDefaultLocator().Append(
                            propertyName));
                }
            }
        }
    }

    return locators;
}

PXR_NAMESPACE_CLOSE_SCOPE
