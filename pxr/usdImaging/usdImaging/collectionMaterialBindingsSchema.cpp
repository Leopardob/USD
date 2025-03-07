//
// Copyright 2023 Pixar
//
// Licensed under the terms set forth in the LICENSE.txt file available at
// https://openusd.org/license.
//
////////////////////////////////////////////////////////////////////////

/* ************************************************************************** */
/* **                                                                      ** */
/* ** This file is generated by a script.                                  ** */
/* **                                                                      ** */
/* ** Do not edit it directly (unless it is within a CUSTOM CODE section)! ** */
/* ** Edit hdSchemaDefs.py instead to make changes.                        ** */
/* **                                                                      ** */
/* ************************************************************************** */

#include "pxr/usdImaging/usdImaging/collectionMaterialBindingsSchema.h"

#include "pxr/imaging/hd/retainedDataSource.h"

#include "pxr/base/trace/trace.h"

// --(BEGIN CUSTOM CODE: Includes)--

#include "pxr/usdImaging/usdImaging/collectionMaterialBindingSchema.h"

// --(END CUSTOM CODE: Includes)--

PXR_NAMESPACE_OPEN_SCOPE

TF_DEFINE_PUBLIC_TOKENS(UsdImagingCollectionMaterialBindingsSchemaTokens,
    USD_IMAGING_COLLECTION_MATERIAL_BINDINGS_SCHEMA_TOKENS);

// --(BEGIN CUSTOM CODE: Schema Methods)--

TfTokenVector
UsdImagingCollectionMaterialBindingsSchema::GetPurposes() const
{
    if (HdContainerDataSourceHandle h = GetContainer()) {
        return h->GetNames();
    }

    return {};
}

UsdImagingCollectionMaterialBindingVectorSchema
UsdImagingCollectionMaterialBindingsSchema::
GetCollectionMaterialBindings() const
{
    return GetCollectionMaterialBindings(
            UsdImagingCollectionMaterialBindingsSchemaTokens->allPurpose);
}

UsdImagingCollectionMaterialBindingVectorSchema
UsdImagingCollectionMaterialBindingsSchema::GetCollectionMaterialBindings(
    TfToken const &purpose) const
{
    return UsdImagingCollectionMaterialBindingVectorSchema(
            _GetTypedDataSource<HdVectorDataSource>(purpose));
}

// --(END CUSTOM CODE: Schema Methods)--

/*static*/
UsdImagingCollectionMaterialBindingsSchema
UsdImagingCollectionMaterialBindingsSchema::GetFromParent(
        const HdContainerDataSourceHandle &fromParentContainer)
{
    return UsdImagingCollectionMaterialBindingsSchema(
        fromParentContainer
        ? HdContainerDataSource::Cast(fromParentContainer->Get(
                UsdImagingCollectionMaterialBindingsSchemaTokens->collectionMaterialBindings))
        : nullptr);
}

/*static*/
const TfToken &
UsdImagingCollectionMaterialBindingsSchema::GetSchemaToken()
{
    return UsdImagingCollectionMaterialBindingsSchemaTokens->collectionMaterialBindings;
}

/*static*/
const HdDataSourceLocator &
UsdImagingCollectionMaterialBindingsSchema::GetDefaultLocator()
{
    static const HdDataSourceLocator locator(GetSchemaToken());
    return locator;
} 

PXR_NAMESPACE_CLOSE_SCOPE