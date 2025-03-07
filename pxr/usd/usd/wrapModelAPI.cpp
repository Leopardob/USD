//
// Copyright 2016 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
#include "pxr/usd/usd/modelAPI.h"
#include "pxr/usd/usd/schemaBase.h"

#include "pxr/usd/sdf/primSpec.h"

#include "pxr/usd/usd/pyConversions.h"
#include "pxr/base/tf/pyContainerConversions.h"
#include "pxr/base/tf/pyResultConversions.h"
#include "pxr/base/tf/pyUtils.h"
#include "pxr/base/tf/wrapTypeHelpers.h"

#include "pxr/external/boost/python.hpp"

#include <string>

PXR_NAMESPACE_USING_DIRECTIVE

using namespace pxr_boost::python;

namespace {

#define WRAP_CUSTOM                                                     \
    template <class Cls> static void _CustomWrapCode(Cls &_class)

// fwd decl.
WRAP_CUSTOM;


static std::string
_Repr(const UsdModelAPI &self)
{
    std::string primRepr = TfPyRepr(self.GetPrim());
    return TfStringPrintf(
        "Usd.ModelAPI(%s)",
        primRepr.c_str());
}

} // anonymous namespace

void wrapUsdModelAPI()
{
    typedef UsdModelAPI This;

    class_<This, bases<UsdAPISchemaBase> >
        cls("ModelAPI");

    cls
        .def(init<UsdPrim>(arg("prim")))
        .def(init<UsdSchemaBase const&>(arg("schemaObj")))
        .def(TfTypePythonClass())

        .def("Get", &This::Get, (arg("stage"), arg("path")))
        .staticmethod("Get")

        .def("GetSchemaAttributeNames",
             &This::GetSchemaAttributeNames,
             arg("includeInherited")=true,
             return_value_policy<TfPySequenceToList>())
        .staticmethod("GetSchemaAttributeNames")

        .def("_GetStaticTfType", (TfType const &(*)()) TfType::Find<This>,
             return_value_policy<return_by_value>())
        .staticmethod("_GetStaticTfType")

        .def(!self)


        .def("__repr__", ::_Repr)
    ;

    _CustomWrapCode(cls);
}

// ===================================================================== //
// Feel free to add custom code below this line, it will be preserved by 
// the code generator.  The entry point for your custom code should look
// minimally like the following:
//
// WRAP_CUSTOM {
//     _class
//         .def("MyCustomMethod", ...)
//     ;
// }
//
// Of course any other ancillary or support code may be provided.
// 
// Just remember to wrap code in the appropriate delimiters:
// 'namespace {', '}'.
//
// ===================================================================== //
// --(BEGIN CUSTOM CODE)--

#include "pxr/base/tf/pyEnum.h"
#include "pxr/base/tf/pyStaticTokens.h"

namespace {

static TfToken _GetKind(const UsdModelAPI &self) {
    TfToken result;
    self.GetKind(&result);
    return result;
}

static SdfAssetPath _GetAssetIdentifier(const UsdModelAPI &self) {
    SdfAssetPath identifier;
    self.GetAssetIdentifier(&identifier);
    return identifier;
}

static std::string _GetAssetName(const UsdModelAPI &self) {
    std::string assetName;
    self.GetAssetName(&assetName);
    return assetName;
}

static std::string _GetAssetVersion(const UsdModelAPI &self) {
    std::string version;
    self.GetAssetVersion(&version);
    return version;
}

static VtArray<SdfAssetPath> _GetPayloadAssetDependencies(const UsdModelAPI &self) {
    VtArray<SdfAssetPath> assetDeps;
    self.GetPayloadAssetDependencies(&assetDeps);
    return assetDeps;
}

static VtDictionary _GetAssetInfo(const UsdModelAPI &self) {
    VtDictionary info;
    self.GetAssetInfo(&info);
    return info;
}


WRAP_CUSTOM {

    TF_PY_WRAP_PUBLIC_TOKENS("AssetInfoKeys", UsdModelAPIAssetInfoKeys,
                             USDMODEL_ASSET_INFO_KEYS);
    {
        scope parent = _class;
        // This must be defined before KindValidationModelHierarchy is used
        // as a default argument to validation.
        TfPyWrapEnum<UsdModelAPI::KindValidation>();
        _class
            .def("GetKind", _GetKind)
            .def("SetKind", &UsdModelAPI::SetKind, arg("value"))
            .def("IsKind", &UsdModelAPI::IsKind,
                 (arg("baseKind"),
                  arg("validation")=UsdModelAPI::KindValidationModelHierarchy))
            .def("IsModel", &UsdModelAPI::IsModel)
            .def("IsGroup", &UsdModelAPI::IsGroup)

            .def("GetAssetIdentifier", _GetAssetIdentifier)
            .def("SetAssetIdentifier", &UsdModelAPI::SetAssetIdentifier)
            .def("GetAssetName", _GetAssetName)
            .def("SetAssetName", &UsdModelAPI::SetAssetName)
            .def("GetAssetVersion", _GetAssetVersion)
            .def("SetAssetVersion", &UsdModelAPI::SetAssetVersion)
            .def("GetPayloadAssetDependencies", _GetPayloadAssetDependencies)
            .def("SetPayloadAssetDependencies", 
                 &UsdModelAPI::SetPayloadAssetDependencies)
            .def("GetAssetInfo", _GetAssetInfo)
            .def("SetAssetInfo", &UsdModelAPI::SetAssetInfo)
            ;
    }
}

} // anonymous namespace
